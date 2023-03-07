# envir.py

import os
import sys
from pathlib import Path
from enum import Enum
import logging

from conda.base.context import context, user_rc_path
import new_conda_env.processing as proc
# ..........................................................................

# unused:
logr_envir = logging.getLogger(__name__)
logr_envir.setLevel(logging.ERROR)

sh = logging.StreamHandler()
formatter = logging.Formatter('%(name)-15s: %(levelname)-8s %(message)s')
sh.setFormatter(formatter)
logr_envir.addHandler(sh)


msgf_create_env = """
    If necessary, you can open the file to tweak it (e.g. the networkx
    package can be removed from the pip deps and added to the conda deps).

    You can now create the new environment with this command:
    `conda env create -f {}`
"""


msg_warn = """
    [ATTENTION]:
    Even if the new environmental yaml file creation is successful,
    that does not mean the env is satisfiable.
    The only way to find out at the moment* is by running the 
    `conda env create -f` command with the file path.

    * There is a feature request (github.com/conda issue #7495) to have
    `conda env create` do a dry-run, which is what would have been used 
    in this project.
    ...And `conda update` does not use a yaml file, so it is not an option.
"""

jp = Path.joinpath

        
class CondaEnvir:
    """CondaEnvir is a class that gathers basic information
    about the current conda setup in order to perform the
    'quick-clone'* of a conda environment when, e.g. a new 
    version of the (python) kernel is needed.
    Call: CondaEnvir(old_ver: str,
                     new_ver: str,
                     dotless_ver: bool,
                     env_to_clone: str, 
                     new_env_name: str="default",
                     kernel: str="python",
                     display_new_yml: bool=True,
                     log_level: str="ERROR")
    [* see README.md]
    
    Arguments:
    - old_ver (str): Previous kernel (python) version
    - new_ver (str): New kernel (python) version
    - dotless_ver (bool): If True, period(s) in new_ver are removed when forming
      the default `new_env_name`
    - env_to_clone (str): The existing conda environment to 'quick-clone'
    - new_env_name (str, "default"): If called with default value, the name
      follows this pattern: env{self.kernel[:2]}{self.new_ver.replace('.','')}",
      e.g.: envpy311
    - kernel (str, "python"): current implementation is for python only
    - display_new_yml (bool, True): output contents?
    - log_level (str, "ERROR"): to set class logging level.
    """
    
    def __init__(self,
                 old_ver: str="",
                 new_ver: str="",
                 dotless_ver: bool=True,
                 env_to_clone: str="",
                 new_env_name: str="default",
                 kernel: str="python",
                 display_new_yml: bool=True,
                 log_level: str="ERROR"):
        
        self.log = logging.getLogger("new_conda_env.envir.CondaEnvir")
        self.log.setLevel(log_level)
        
        self.kernel = kernel.lower()
            
        if old_ver == "" or new_ver == "":
            msg = "Missing version: empty old_ver or new_ver str."
            self.log.error(msg)
            raise ValueError(msg)

        if (new_ver == old_ver):
            # no problem: user wants a "lean" yml file
            self.log.warning("The old & new versions are identical.")
            
        self.conda_root = Path(os.getenv("CONDA_ROOT"))
        self.basic_info = self.get_conda_info()
        self.user_dir = self.basic_info["user_condarc"].parent
        
        self.env_to_clone = env_to_clone
        old_prefix = jp(self.basic_info["env_dir"], self.env_to_clone)
        if not old_prefix.exists():
            msg = "Typo in <env_to_clone>? "
            msg = msg + f"Path not found: {old_prefix})"
            self.log.error(msg)
            raise FileNotFoundError
            
        self.old_ver = old_ver
        self.new_ver = new_ver
        self.dotless_ver = dotless_ver
        self.new_env_name = self.get_new_env_name(new_env_name)
        self.new_prefix = jp(self.basic_info["env_dir"], self.new_env_name)
        self.new_yml = self.get_lean_yml_pathname()
        self.display_new_yml = display_new_yml 
        self.user_rc = self.get_user_rc()
        self.has_user_rc = self.user_rc is not None 


    def get_conda_info(self) -> dict:
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
            self.log.error(msg)
            raise ValueError
        
        d = {"conda_prefix": prefix_conda,
             "active_prefix": prefix_active,
             "user_condarc": Path(user_rc_path),
             # only consider user's .condarc, e.g.: <user path>\miniconda3\\envs
             "env_dir": Path(context.envs_dirs[0]),
             #what about other kernels?
             "default_python": context.default_python # unused
            }
        
        return d

    
    def get_user_rc(self):
        rc = self.basic_info["user_condarc"]
        if rc.exists():
            return rc
        self.log.debug(f"No user-defined .condarc found in: {rc}.")
        
        return None

    
    def get_rc_python_deps(self) -> bool:
        """The key 'add_pip_as_python_dependency' in condarc
        is True by default. Even so, the 3 packages it refers to 
        (pip, setuptools & wheel), will not be listed using the
        '--from-history' export flag (but all those listed under the
        `create_default_packages` key will).
        Return the key value from user's rc if set False, else True.
        """
        out = True
        if self.has_user_rc:
            rc = proc.yaml_round_trip_load(self.user_rc)
            out = rc.get("add_pip_as_python_dependency")
            if out is not None and not out:
                return out
        return out


    def get_new_env_name(self, str_name):
        if str_name == "default":  # def name is dotless
            to_ver = self.new_ver.replace('.','')
            return f"env{self.kernel[:2]}{to_ver}"
        
        if self.dotless_ver:
            return str_name.replace('.','')
        
        return str_name


    def get_lean_yml_pathname(self) -> Path:
        """Name of the output yml file produced by new_conda_env.
        Pattern: lean_<new_env>_from_<env_to_clone>.yml"
        """
        new_env = self.new_env_name.replace('.','')
        from_env = self.env_to_clone.replace('.','')
        n = f"lean_{new_env}_from_{from_env}.yml" 

        return jp(self.user_dir, n)


    @staticmethod
    def get_export_cmd(env_name:str, flag: str) -> str:
        cmd = "conda env export -n {} {}"
        return cmd.format(env_name, flag)

    
    def get_export_stream(self, cmd: str) -> str:
        """Return stream from subprocess.Popen using the 
        conda env export cmd.
        """
        self.log.debug(f"Running cmd: {cmd}")
        stream = proc.run_export(cmd)

        return stream


    def _show_final_msg(self):
        final_env = self.new_yml
        if not final_env.exists():
            msg = "Oops: final file not found!\n"
            msg = msg + f"\t{final_env}"
            self.log.error(msg)
            raise FileNotFoundError(msg)

        if self.display_new_yml:
            print(f"\nFinal environment file: {final_env}\n")
            print(final_env.read_text())

        print(msgf_create_env.format(final_env))
        print(msg_warn)

    
    def get_new_env_yaml(self) -> Path:
        """Perform these step to create the final new_env_yaml:
        1. Retrieve the pip dependencies dict from nobld_export stream & strip
        their versions.
        2. Update hist_export stream with data from .condarc (if found) and new env
        3. Save the new data as per self.new_yml.name
        """

        # pip deps from --no-builds export stream
        NOBLD = "--no-builds"
        cmd = self.get_export_cmd(self.env_to_clone, NOBLD)
        stream_nobld = self.get_export_stream(cmd)
        yml_nobld = proc.load_as_yml(stream_nobld)

        clean_pips = proc.get_pip_deps(yml_nobld)
        #del yml_nobld
                 
        # update of --from-history export stream
        HIST = "--from-history"
        cmd = self.get_export_cmd(self.env_to_clone, HIST)
        stream_hist = self.get_export_stream(cmd)
        yml_his = proc.load_as_yml(stream_hist)

        self.log.debug(f"> yml_his:\n{yml_his}")
                 
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
        yml_his["dependencies"].insert(1, "pip")

        has_wheel = False
        has_stt = False
        for i, mapping in enumerate(yml_his["dependencies"]):
            if mapping == old_ker_name:
                 _ = yml_his["dependencies"].pop(i)
            else:
                 has_wheel = has_wheel or (mapping == "setuptools")
                 has_stt = has_stt or (mapping == "wheel")
        
        if self.get_rc_python_deps():
            if not has_stt:
                yml_his["dependencies"].append("setuptools")
            if not has_wheel:
                yml_his["dependencies"].append("wheel")

        # Finally add the pip deps from the 'long' yaml:
        if clean_pips is not None:
            self.log.debug(f"> clean_pips:\n{clean_pips}")
            yml_his["dependencies"].append(clean_pips)
        else:
            self.log.debug(f"> No pip deps found.")

        proc.save_to_yml(self.new_yml, yml_his)

        self._show_final_msg()
        

    def __repr__(self):
        import inspect
        return self.__class__.__name__ + str(inspect.signature(self.__class__))
                        

    def __str__(self):
        return f"DOC: {self.__doc__}\n{msg_warn}"
