# processing.py

import os
import sys
from pathlib import Path
import re
from functools import partial
from logging import getLogger
from subprocess import Popen, PIPE
        
try:
    import ruamel.yaml as yaml
except ImportError:
    try:
        import ruamel_yaml as yaml
    except ImportError:
        raise ImportError("No yaml library available. To proceed, conda install ruamel.yaml")

from conda.common.serialize import yaml_round_trip_load
        
# To create temp files?: see conda/gateways/disk/create.py 
# ..........................................................................

log = getLogger(__name__)

winOS = sys.platform == "win32"

def path2str0(p: Path, win_os: bool=True):
    s = str(p) if win_os else p.as_posix()
    return s

path2str = partial(path2str0, win_os=winOS)


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
