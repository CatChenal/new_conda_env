# envir.py

import os
import sys
from pathlib import Path
from enum import Enum
from logging import getLogger

from conda.base.context import context, user_rc_path
import new_conda_env.processing as proc
# ..........................................................................

log = getLogger(__name__)

jp = Path.joinpath

class CondaFlag(Enum):
    NOBLD = "--no-builds"
    HIST = "--from-history"

        
class CondaEnvir:
    """CondaEnvir is a class that gathers basic information
    about the current conda setup in order to perform the
    'quick-clone'* of a conda environment when, e.g. a new 
    version of the (python) kernel is needed.
    Call: CondaEnvir(old_ver: str, new_ver: str, dotless_ver: bool,
                     env_to_clone: str, new_env_name: str="default",
                     kernel: str="python",
                     debug: bool=True)
    [* see README.md]
    
    Arguments:
    - old_ver (str): Previous python version
    - new_ver (str): New python version
    - dotless_ver (bool): If True, period(s) in new_ver are removed when forming
      the default `new_env_name`
    - env_to_clone (str): The existing conda environment to 'quick-clone'
    - new_env_name (str, "default"): If called with default value, the new env name
      will have this pattern: "env" + self.new_ver, e.g. env3.11 or env311
    - kernel (str, "python"): current implementation is for python only
    - display_new_yml (bool, True): output contents?
    - debug (bool, True): flag for tracing calls.
    """
    
    def __init__(self,
                 old_ver: str="", new_ver: str="", dotless_ver: bool=True,
                 env_to_clone: str="", new_env_name: str="default",
                 kernel: str="python",
                 display_new_yml: bool=True,
                 debug: bool=True):
        
        self.kernel = kernel.lower()
        if self.kernel != "python":
            log.error("Post an enhancement issue!")
            raise NotImplementedError
        if old_ver == "" or new_ver == "":
            msg = "Missing version of old_ver or new_ver (empty string)."
            log.error(msg)
            raise ValueError(msg)
            
        if (new_ver == old_ver):
            # no problem: user wants a "lean" yml file
            log.warning("The old & new versions are identical.")

        self.conda_root = Path(os.getenv("CONDA_ROOT"))
        self.basic_info = self.get_conda_info()
        
        self.env_to_clone = env_to_clone
        self.old_prefix = jp(self.basic_info["env_dir"], self.env_to_clone)
        if not self.old_prefix.exists():
            msg = "Typo in <env_to_clone>?"
            msg = msg + f" Path not found: {self.old_prefix})"
            log.error(msg)
            raise FileNotFoundError
            
        self.old_ver = old_ver
        self.dotless_ver = dotless_ver
        self.new_ver = (new_ver.replace('.','') if dotless_ver else new_ver)
        self.new_env_name = self.get_new_env_name(new_env_name)
        # new temp file names:
        self.yml_nobld = self.get_new_yml_name(CondaFlag.NOBLD)
        self.yml_hist = self.get_new_yml_name(CondaFlag.HIST)
        self.intermediate_yamls = None
        
        self.new_prefix = jp(self.basic_info["env_dir"], self.new_env_name)
        self.new_yml = self.get_lean_yml_pathname()
        self.display_new_yml = display_new_yml 
        self.user_rc = self.get_user_rc()
        self.has_user_rc = self.user_rc is not None 
        self.user_dir = self.basic_info["user_condarc"].parent
        
        self.debug = debug
        if self.debug:
            log.debug("Basic info:\n", f"- Root: {self.conda_root}\n",
                      f"- Info dict:\n\t{self.basic_info}")
        
        
    @staticmethod
    def get_conda_info() -> dict:
        """Return minimal number of conda-calculated 
        variables in a dict.
        All paths -> Path objects.
        """
        # check first: active env == base?
        prefix_conda = Path(context.conda_prefix)
        prefix_active = Path(context.active_prefix)
        if prefix_active != prefix_conda:
            msg = "\n`new_cond_env` should be run in (base), but this "
            msg = msg + f"environment is activated: {prefix_active.name}\n"
            msg = msg + "Deactivate it & re-run `new_cond_env`."
            log.error(msg)
            raise ValueError
        
        #check curr path:
        #should be path from just opened conda prompt ==user's?
        # to test: problem with admin-installed conda on linux?
        # or: self.conda_root.parent != Path().home() ???
        if prefix_conda.parent != Path().home():
            msg = """
            `new_cond_env` should be run in the user's home folder, i.e. 
            the path from a just opened conda prompt (with an activated 
            base environment)."""
            log.error(msg)
            raise ValueError
        
        d = {"conda_prefix": prefix_conda,
             "active_prefix": prefix_active,
             "user_condarc": Path(user_rc_path),
             # only consider user's .condarc; 
             # -> relies on ordering + possibly OS: not robust -> test
             "env_dir": Path(context.envs_dirs[0]),
             #what about other kernels?
             "default_python": context.default_python # unused
            }
        
        return d

    
    def get_user_rc(self):
        rc = self.basic_info["user_condarc"]
        if rc.exists():
            return rc
        log.info(f"No user-defined .condarc found in: {rc}.")
        
        return None

    
    def get_rc_python_deps(self) -> bool:
        out = True #:: def. of "add_pip_as_python_dependency"
        if self.has_user_rc:
            rc = proc.load_env_yml(self.user_rc)
            # if key is True, pip, wheel & setuptools 
            # won't be listed in export --from-history
            out = rc.get("add_pip_as_python_dependency")
            if out is not None and not out:
                return out
        return out


    def get_new_env_name(self, str_name):
        if str_name == "default":
            env_name = "env" + self.new_ver
        else:
            env_name = str_name
            
        return env_name


    def get_new_yml_name(self, flag: CondaFlag) -> str:
        """Name of intermediate yml file.
        Pattern: "env_"<env_to_clone>_<CondaFlag name>.yml"
        """
        env = self.env_to_clone.replace('.','')
        return f"env_{env}_{flag.name.lower()}.yml"


    def get_lean_yml_pathname(self) -> Path:
        """Name of the output produced by new_conda_env.
        Pattern: <kernel[:2]><to_env>_from_<env_to_clone>.yml"
        """
        from_env = self.env_to_clone.replace('.','')
        to_env = self.new_ver.replace('.','')
        n = f"env_{self.kernel[:2]}{to_env}_from_{from_env}.yml" 

        return jp(Path().home(), n)


    def get_export_cmd(self, flag: CondaFlag) -> str:
        """Return a str command (list did not work; winOS)"""
        cmd_str = "conda env export -n {} {} --file {}"
        
        fla = CondaFlag[flag.name].value  # enforced typing
        if flag.name == 'HIST':
            yml_path = proc.path2str(jp(self.user_dir,self.yml_hist))
        else:
            yml_path = proc.path2str(jp(self.user_dir,self.yml_nobld))
        cmd_str = cmd_str.format(self.env_to_clone, fla, yml_path)
        if self.debug:
            log.debug(f".get_export_cmd:: {cmd_str}")

        return cmd_str


    def create_yamls(self, CondaFlag) -> list[Path]:
        """Create two yaml files using:
        `self.get_export_cmd()` with these flags:
        1. --no-builds: out="env_<env_to_clone>_nobld.yml" ("the long yml")
        2. --from-history: out="env_<env_to_clone>_hist.yml"
        Return the file paths: long yml, short yml
        """
        out = list()

        for i, fla in enumerate([CondaFlag.NOBLD, CondaFlag.HIST]):
            # save Path obj:
            out.append(jp(self.user_dir, self.get_new_yml_name(fla)))

            cmd = self.get_export_cmd(fla)
            if self.debug:
                log.debug(f"Executing command :: {cmd}")
                
            proc.run_export(cmd)
            
            log.info(f"'Env file created: {proc.path2str(out[i])}")

        self.intermediate_yamls = out
        return


    def create_new_env_yaml(self) -> Path:
        """Perform these step to create the final new_env_yaml:
        1. Retrieve the pip dependencies dict from nobld_yml & strip
        their versions.
        2. Update hist_yml with data from .condarc (if found) and new env
        3. Save the new data as per self.new_yml.name
        """
        def show_final_msg(self, final_env):
            if not final_env.exists():
                raise FileNotFoundError("Oops: final file not found!")

            if self.intermediate_yamls:
                msg = "\nThese intermediate files can be deleted:\n"
                msg = msg + " - {}\n - {}".format(*self.intermediate_yamls)
                log.info(msg)
                print(msg)

            if self.display_new_yml:
                print(f"\nFinal environment file: {final_env}\n")
                print(final_env.read_text())
            
            msg = "\nYou can now create the new environment with this command:\n"
            msg = msg + f">conda env create -f {final_env}\n\n"
            log.info(msg)
            print(msg)
                
        yml_nobld_path = jp(self.user_dir, self.yml_nobld)
        assert yml_nobld_path.exists()

        yml_nob = proc.load_env_yml(yml_nobld_path)
        clean_pips = proc.get_pip_deps(yml_nob)
        del yml_nob
        
        yml_hist_path = jp(self.user_dir, self.yml_hist)
        assert yml_hist_path.exists()

        old_ker_name = self.kernel + "=" + self.old_ver
        new_ker_ver = self.kernel + "=" + self.new_ver

        new_path = jp(self.user_dir, self.new_yml.name)
        log.info(f"New yml filepath: {new_path}")

        # hist
        yml_his = proc.load_env_yml(yml_hist_path)

        # reset name and prefix keys:
        yml_his["name"] = self.new_env_name
        yml_his["prefix"] = proc.path2str(self.new_prefix)

        # add new kernel ver as 1st dep:
        if yml_his["dependencies"][0] != new_ker_ver:
            yml_his["dependencies"].insert(0, new_ker_ver)

        whe_setools = []
        for i, mapping in enumerate(yml_his["dependencies"]):
            if mapping == old_ker_name:
                _ = yml_his["dependencies"].pop(i)
            if mapping.startswith("setuptools=") or mapping.startswith("wheel="):
                whe_setools.append(mapping)
        
        at_end = i + 1
        if self.get_rc_python_deps():
            if not whe_setools:
                #print("no wheel or setuptools")
                yml_his["dependencies"].append("setuptools")
                yml_his["dependencies"].append("wheel")
                at_end += 2
            elif len(whe_setools) == 1:
                which = "setuptools"
                if whe_setools[0] == which: # found, other missing
                    which = "wheel"
                yml_his["dependencies"].append(which)
                at_end += 1
                
        yml_his["dependencies"].append("pip")
        at_end += 1
        yml_his["dependencies"].insert(at_end, clean_pips)

        proc.save_to_yml(new_path, yml_his)

        show_final_msg(self, new_path)
        
        
    def __repr__(self):
        import inspect
        return self.__class__.__name__ + str(inspect.signature(self.__class__))
                        

    def __str__(self):
        return f"DOC: {self.__doc__}"
