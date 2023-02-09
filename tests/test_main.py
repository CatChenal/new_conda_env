# test_main.py
import os
import sys
from pathlib import Path
from functools import partial

from logging import getLogger
import subprocess
from subprocess import Popen, PIPE

import unittest
import pytest

from new_conda_env import main

#.........................................................
    
def test_get_export_cmd():
    env_to_clone = 'ds310'
    flag = CondaFlag.HIST
    
    user_dir = DIR_TMP
    yml_file = f"env_{env_to_clone}_{fla.name.lower()}.yml"
    yml_path = main.path2str(user_dir.joinpath(yml_file))
        
    #cmd_list = get_export_cmd(env_to_clone, flag, yml_path)
    return get_export_cmd(env_to_clone, flag, yml_path)


def test_run_export():
    cmd = test_get_export_cmd()
    run_export(cmd)
    return
    
def test_create_yamls():
    env_to_clone = 'ds310'
    user_dir = DIR_TMP
    
    new_yamls = create_yamls(env_to_clone, user_dir)
    
    yml_n = get_new_yml_name(env_to_clone, CondaFlag.NOBLD)
    yml_n_path = user_dir.joinpath(yml_n)
    assert new_yamls[0] == yml_n_path
    
    yml_h = get_new_yml_name(env_to_clone, CondaFlag.HIST)
    yml_h_path = user_dir.joinpath(yml_h)
    assert new_yamls[1] == yml_h_path
    
    


