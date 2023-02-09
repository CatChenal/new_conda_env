import os
import sys
from pathlib import Path
import re
from functools import partial
from enum import Enum
from logging import getLogger
import subprocess
from subprocess import Popen, PIPE, list2cmdline

try:
    import ruamel.yaml as yaml
except ImportError:
    try:
        import ruamel_yaml as yaml
    except ImportError:
        raise ImportError("No yaml library found. To proceed, conda install ruamel.yaml")
        
from conda.base.context import context, user_rc_path  #, sys_rc_path
from conda.common.serialize import yaml_round_trip_dump, _yaml_round_trip, yaml_round_trip_load
# To create temp files?:
# see conda/gateways/disk/create.py 
# ..........................................................................

log = getLogger(__name__)

winOS = sys.platform == "win32"

def path2str0(p: Path, win_os: bool=True):
    s = str(p) if win_os else p.as_posix()
    return s

path2str = partial(path2str0, win_os=winOS)


class CondaFlag(Enum):
    NOBLD = "--no-builds"
    HIST = "--from-history"    


def run_export(args: str):
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    stdout = stdout.decode()
    try:
        assert proc.returncode == 0
    except Exception as e:
        # print output and rethrow exception
        log.debug(args)
        log.debug("--- stdout ---")
        for line in stdout.splitlines():
            log.debug(line)
        log.debug("--- stderr ---")
        for line in stderr.splitlines():
            log.debug(line)
        log.debug("--- end ---")

        raise e  

        
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
      will have this pattern: "env" + self.new_ver, e.g. env3.11
    - kernel (str, "python"): current implementation is for python only
    - debug (bool, True): flag for tracing calls (temp?).
    """
    
    def __init__(self,
                 old_ver: str, new_ver: str, dotless_ver: bool,
                 env_to_clone: str, new_env_name: str="default",
                 kernel: str="python",
                 debug: bool=True):
        
        self.kernel = kernel.lower()
        if self.kernel != "python":
            log.error("Post an enhancement issue!")
            raise NotImplementedError
          
        if (new_ver == old_ver):
            # no problem: user wants a "lean" yml file
            log.warning("The old & new versions are identical.")

        self.conda_root = Path(os.getenv("CONDA_ROOT"))
        self.basic_info = self.get_conda_info()
        
        self.env_to_clone = env_to_clone
        self.old_prefix = (self.basic_info["env_dir"]
                            .joinpath(self.env_to_clone))
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
        
        self.new_prefix = self.basic_info["env_dir"].joinpath(self.new_env_name)
        self.new_yml = self.get_lean_yml_pathname()
        
        self.user_rc = self.get_user_rc()
        self.has_user_rc = self.user_rc is not None 
        self.user_dir = Path().home()
        
        self.debug = debug
        if debug:
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
             "default_python": context.default_python # not used
            }
        
        return d

    
    def get_new_yml_name(self, flag: CondaFlag) -> str:
        """Name of intermediate yml file."""
        env = self.env_to_clone.replace('.','')
        return f"env_{env}_{flag.name.lower()}.yml"
    
    
    def get_lean_yml_pathname(self) -> Path:
        """Name of the output produced by new_conda_env."""
        from_env = self.env_to_clone.replace('.','')
        to_env = self.new_ver.replace('.','')
        n = f"env_{self.kernel[:2]}{to_env}_from_{from_env}.yml" 

        return Path().home().joinpath(n)


    def get_export_cmd(self, flag: CondaFlag) -> str:
        """Return a str command (list did not work; winOS)"""
        cmd_str = "conda env export -n {} {} --file {}"
        fla = CondaFlag[flag.name].value  # enforced typing
        if flag.name == 'HIST':
            yml_path = path2str(self.yml_hist)
        else:
            yml_path = path2str(self.yml_nobld)
        cmd_str = cmd_str.format(self.env_to_clone, fla, yml_path)
        log.debug(f".get_export_cmd:: {cmd_str}")

        return cmd_str

    
    def get_user_rc(self):
        rc = self.basic_info["user_condarc"]
        if rc.exists():
            return rc
        log.info(f"No user-defined .condarc found in: {rc}.")
        
        return None

    
    def get_rc_python_deps(self) -> bool:
        out = True #:: def. of "add_pip_as_python_dependency"
        if self.has_user_rc:
            rc = load_env_yml(self.user_rc)
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
    

    def create_yamls(self) -> list[Path]:
        """Create two yaml files using:
        `conda env export -n <env_to_clone> <flag> > <out>` with these flags:
        1. --no-builds: out="env_<env_to_clone>_nobld.yml" ("the long yml")
        2. --from-history: out="env_<env_to_clone>_hist.yml"
        Return the file paths: long yml, short yml
        """
        out = list()

        for i, fla in enumerate([CondaFlag.NOBLD, CondaFlag.HIST]):
            yml_file = get_new_yml_name(self.env_to_clone, fla)
            out.append(self.user_dir.joinpath(yml_file))  # Path obj
            yml_path = path2str(out[i])
            cmd = get_export_cmd(self.env_to_clone, fla, yml_path)

            log.debug(f"Executing command :: {cmd}")
            run_export(cmd)
            log.info(f"'Env file created: {yml_path}")

        return out


    def create_new_env_yaml(self) -> Path:
        """Perform these step to create new_env_yaml:
        1. Retrieve the pip dependencies dict from nobld_yml & strip
        their versions.
        2. Update hist_yml with data from .condarc (if found) and new env
        3. Save the new data as per self.new_yml.name

        """
        ## call create_yamls
        
        yml_nobld_path = self.user_dir.joinpath(self.yml_nobld)
        assert yml_nobld_path.exists()

        yml_nob = load_env_yml(yml_nobld_path)
        clean_pips = get_pip_deps(yml_nob)

        yml_hist_path = self.user_dir.joinpath(self.yml_hist)
        assert yml_hist_path.exists()

        old_ker_name = self.kernel + "=" + self.old_ver
        new_ker_ver = self.kernel + "=" + self.new_ver

        new_path = self.user_dir.joinpath(self.new_yml.name)
        log.info(f"New yml filepath: {new_path}")

        # hist
        yml_his = load_env_yml(yml_hist_path)

        # reset name and prefix keys:
        yml_his["name"] = self.new_env_name
        yml_his["prefix"] = path2str(self.new_prefix)

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

        yml_his["dependencies"].insert(at_end, clean_pips)

        save_to_yml(new_path, yml_his)

        # show:
        if new_path.exists():
            print(new_path.read_text())


    def __repr__(self):
        import inspect
        return self.__class__.__name__ + str(inspect.signature(self.__class__))
                        

    def __str__(self):
        return f"DOC: {self.__doc__}"

    

def load_env_yml(yml_filepath: Path):
    log.info(f"Loading yml file: {path2str(yml_filepath)}\n")
    return yaml_round_trip_load(yml_filepath)   


def save_to_yml(yml_filepath, data):
    yam = yaml.YAML()
    with open(yml_filepath, 'wb') as f:
        yam.dump(data, f)
    log.info(f"File saved to yml: {path2str(yml_filepath)}\n")


def get_pip_deps(data, strip_ver=True):
    """Retrieve pip dict from standard yml file.
    """

    pip_deps = None
    for i, d in enumerate(data["dependencies"]):
        if isinstance(d, dict) and d.get("pip") is not None:
            pip_deps = d
            break
    if not strip_ver or pip_deps is None:
        return pip_deps
    
    # else remove versions
    # {1,}:: at least 1 period in version, e.g. networkx==3.0
    regex = r"(?<=)==\d+(?:\.\d+){1,}"
    cleaned = dict(pip=[re.sub(regex,"",p) for p in pip_deps["pip"]])
        
    return cleaned
