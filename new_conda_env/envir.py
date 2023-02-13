# envir.py

import os
import sys
from pathlib import Path
from enum import Enum
from logging import getLogger

from conda.base.context import context, user_rc_path
import new_conda_env.processing as proc
# ..........................................................................

warn = """
Attention:  Even if the new environmental yaml file
creation is successful, that does not mean the env is satisfiable.
The only way to find out at the moment* is by running the `conda env create -f`
command with the file path.

* There is a feature request (github.com/conda issue #7495) to enable the env 
create command to do a dry-run, which is what would have been used in this project.
"""

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
    - new_env_name (str, "default"): If called with default value, the name
      follows this pattern: env{self.kernel[:2]}{self.new_ver.replace('.','')}",
      e.g.: envpy311
    - kernel (str, "python"): current implementation is for python only
    - display_new_yml (bool, True): output contents?
    - debug (bool, True): flag for tracing calls.
    """
    
    def __init__(self,
                 old_ver: str="",
                 new_ver: str="",
                 dotless_ver: bool=True,
                 env_to_clone: str="",
                 new_env_name: str="default",
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
        old_prefix = jp(self.basic_info["env_dir"], self.env_to_clone)
        if not old_prefix.exists():
            msg = "Typo in <env_to_clone>? "
            msg = msg + f"Path not found: {old_prefix})"
            log.error(msg)
            raise FileNotFoundError
            
        self.old_ver = old_ver
        self.new_ver = (new_ver.replace('.','') if dotless_ver else new_ver)
        self.new_env_name = self.get_new_env_name(new_env_name)
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
        out = True #:: "add_pip_as_python_dependency" key
        if self.has_user_rc:
            rc = proc.yaml_round_trip_load(self.user_rc)
            # even if key is True, pip, wheel & setuptools 
            # won't be listed in export --from-history
            out = rc.get("add_pip_as_python_dependency")
            if out is not None and not out:
                return out
        return out


    def get_new_env_name(self, str_name):
        if str_name == "default":
            to_ver = self.new_ver.replace('.','')
            env_name = f"env{self.kernel[:2]}{to_ver}"
        else:
            env_name = str_name
            
        return env_name


    def get_lean_yml_pathname(self) -> Path:
        """Name of the output produced by new_conda_env.
        Pattern: env_<kernel[:2]><to_env>_from_<env_to_clone>.yml"
        """
        from_env = self.env_to_clone.replace('.','')
        new_env = self.new_env_name.replace('.','')
        n = f"env_{new_env}_from_{from_env}.yml" 

        return jp(Path().home(), n)


    def get_export_stream(self, flag: CondaFlag) -> str:
        """Return stream from subprocess.Popen using the 
        conda env export cmd with either the --no-buils or 
        --from-history flag as fiven by fla.
        """
        fla = CondaFlag[flag.name].value
        cmd = f"conda env export -n {self.env_to_clone} {fla}"
        log.info(f"Running cmd: {cmd}")
        
        stream = proc.run_export(cmd)

        return stream


    def _show_final_msg(self, final_env):
        if not final_env.exists():
            raise FileNotFoundError("Oops: final file not found!")

        if self.display_new_yml:
            print(f"\nFinal environment file: {final_env}\n")
            print(final_env.read_text())

        msg = "\nYou can now create the new environment with this command:\n"
        msg = msg + f">conda env create -f {final_env}\n\n"
        log.info(msg)
        print(msg)

        
    def create_new_env_yaml(self) -> Path:
        """Perform these step to create the final new_env_yaml:
        1. Retrieve the pip dependencies dict from nobld_export stream & strip
        their versions.
        2. Update hist_export stream with data from .condarc (if found) and new env
        3. Save the new data as per self.new_yml.name
        """ 
        # output filepath
        new_path = jp(self.user_dir, self.new_yml.name)
        
        # pip deps from --no-builds export stream
        stream_nobld = self.get_export_stream(CondaFlag.NOBLD) 
        clean_pips = proc.get_pip_deps(proc.yaml_round_trip_load(stream_nobld))

        # update of --from-history export stream
        stream_hist = self.get_export_stream(CondaFlag.HIST)
        yml_his = proc.yaml_round_trip_load(stream_hist)

        old_ker_name = self.kernel
        new_ker_ver = old_ker_name + "=" + self.new_ver
        old_ker_name = old_ker_name + "=" + self.old_ver 

        # reset name and prefix keys:
        yml_his["name"] = self.new_env_name
        yml_his["prefix"] = proc.path2str(self.new_prefix)

        # add new kernel ver as 1st dep:
        if yml_his["dependencies"][0] != new_ker_ver:
            yml_his["dependencies"].insert(0, new_ker_ver)
        # add pip:
        yml_his["dependencies"].insert(1,"pip")

        py_deps = []
        for i, mapping in enumerate(yml_his["dependencies"]):
            if mapping == old_ker_name:
                _ = yml_his["dependencies"].pop(i)
            if mapping.startswith("setuptools") or mapping.startswith("wheel"):
                py_deps.append(mapping)

            at_end = i + 1
            if self.get_rc_python_deps():
                if not py_deps:
                    #print("no wheel or setuptools")
                    yml_his["dependencies"].append("setuptools")
                    yml_his["dependencies"].append("wheel")
                    at_end += 2
                elif len(py_deps) == 1:
                    which = "setuptools"
                    if py_deps[0] == which: # found, other missing
                        which = "wheel"
                    yml_his["dependencies"].append(which)
                    at_end += 1

            # Finally add the pip dependencies from the 'long' yaml:
            if clean_pips:
                at_end += 1
                yml_his["dependencies"].insert(at_end, clean_pips)

            proc.save_to_yml(new_path, yml_his)

            self._show_final_msg(new_path)
        
        
        
    def __repr__(self):
        import inspect
        return self.__class__.__name__ + str(inspect.signature(self.__class__))
                        

    def __str__(self):
        return f"DOC: {self.__doc__}\n{warn}"
