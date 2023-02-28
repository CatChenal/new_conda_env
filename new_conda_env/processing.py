# processing.py

import sys
from pathlib import Path
import re
from functools import partial
import subprocess
import logging

from conda.common.serialize import yaml_round_trip_load, yaml_round_trip_dump
# ..........................................................................

log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)

sh = logging.StreamHandler()
formatter = logging.Formatter('%(name)-15s: %(levelname)-8s %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


winOS = sys.platform == "win32"


def path2str0(p: Path, win_os: bool=True):
    s = str(p) if win_os else p.as_posix()
    return s

path2str = partial(path2str0, win_os=winOS)


def run_export(args: str, timout: int=60):

    proc = subprocess.run(args, capture_output=True, text=True)
    try:   
        proc.check_returncode()
        
        if proc.returncode == 0:
            outs = proc.stdout
            
            if not outs:
                msg = "No output. If this is a surprise, "
                msg = msg + "perhaps the command redirected results "
                msg = msg + "to a file?\n"
                msg = msg + "The `run` command used these args= {}".format(*args)
                log.debug(msg)
                print(msg)

    except subprocess.TimeoutExpired:
        proc.kill()
        log.debug("The `run` command timed out!")
        
    except Exception as err:
        errs = proc.stderr
        log.debug(f"Unexpected err {errs}, {type(err)}")
        raise
        
    return outs


def save_to_yml(yml_filepath, data):
    with open(yml_filepath, 'wb') as f:
        yaml_round_trip_dump(data, f)
    log.debug(f"File saved to yml: {path2str(yml_filepath)}\n")


def load_as_yml(yml_stream):
    data = yaml_round_trip_load(yml_stream)
    return data


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
    regex = r"(?<=)==\d+(?:\.\d*){0,}"
    cleaned = dict(pip=[re.sub(regex,"",p) for p in pip_deps["pip"]])
        
    return cleaned
