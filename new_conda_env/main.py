import os
import sys
from pathlib import Path
import re
from functools import partial
from logging import getLogger
import subprocess
from subprocess import Popen, PIPE

try:
    import ruamel.yaml as yaml
except ImportError:
    try:
        import ruamel_yaml as yaml
    except ImportError:
        raise ImportError("No yaml library found. To proceed, conda install ruamel.yaml")
        
from conda.base.context import context, user_rc_path  #, sys_rc_path
from conda.common.serialize import yaml_round_trip_dump, _yaml_round_trip, yaml_round_trip_load
# ..........................................................................

log = getLogger(__name__)

winOS = sys.platform == "win32"

def path2str0(p: Path, win_os: bool=True):
    s = str(p) if win_os else p.as_posix()
    return s

path2str = partial(path2str0, win_os=winOS)


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
        self.new_prefix = self.basic_info["env_dir"].joinpath(self.new_env_name)
        self.new_yml = self.get_new_yml_pathname()
        
        self.user_rc = self.get_user_rc()
        self.has_user_rc = self.user_rc is not None 
        
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


    def get_new_yml_pathname(self) -> Path:
        from_env = self.env_to_clone.replace('.','')
        to_env = self.new_ver.replace('.','')
        n = f"lean_env_from_{from_env}_to_{to_env}.yml" 
        
        return Path().home().joinpath(n)


    def get_user_rc(self):
        rc = self.basic_info["user_condarc"]
        if rc.exists():
            return rc
        log.info(f"No user-defined .condarc found in: {rc}.")
        
        return None

    
    def get_rc_python_deps(self) -> bool:
        out = True #:: rc key "add_pip_as_python_dependency" def.
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

    
    def run_conda_export(self) -> None:
        """
        WIP
        Run 
        1. `conda export` with --no-builds flag > self.env_to_clone+'_nobld'.yml
        2. `conda export` with --from-history flag > self.env_to_clone+'_hist'.yml
        """
        if self.debug:
            user_dir = Path.cwd().parent.joinpath('_temp')
        else:
            user_dir = self.basic_info['conda_prefix'].parent
        
        ok = False
        yml_nobld_path = user_dir.joinpath(test_yml_nobld)
        # create & check outcome
        yml_nobld_path.exists()

        yml_hist_path = user_dir.joinpath(test_yml_hist)
        # create & check outcome
        yml_hist_path.exists()

        return yml_hist_path, yml_nobld_path

    
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
