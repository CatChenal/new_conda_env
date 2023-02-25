# test_envir.py

import sys

from enum import Enum
from pathlib import Path

import unittest
from unittest import mock
import pytest

from new_conda_env import envir, processing as proc

#.........................................................

class CondaFlag(Enum):
    NOBLD = "--no-builds"
    HIST = "--from-history"
    
CONTENT = "content"

DIR_TMP = tmp_path


"""Need to patch class CondaEnvir to test its methods
"""
# required args:
req_argv = ["-old_ver", "3.10" , "-new_ver", "3.9", 
            "-new_env_name", "ds39", "-env_to_clone", "ds310"]
argv_wrong_kernel = ["-old_ver", "3.10" , "-new_ver", "3.9",
                      "-new_env_name", "ds39", "-env_to_clone", "ds310",
                      "-kernel", "R"]

@pytest.mark.parametrize("argv", [req_argv, argv_wrong_kernel])
@mock.patch.object(new_conda_env.envir.CondaEnvir.get_export_stream, 'get_stream')
@mock.patch.object(new_conda_env.envir.CondaEnvir.create_new_env_yaml, 'new_yml')
def test_CondaEnvir(self, mock_new_yml, mock_get_stream):
    expected = "lean_ds39_from_ds310.yml"
    mock_get_stream.return_value = CONTENT
    mock_new_yml.return_value = expected

    # test argv[0]
    CE = envir.CondaEnvir(argv[0])
    self.assertEqual(CE.old_ver, "3.10")
    self.assertEqual(CE.kernel, "python")
    self.assertEqual(CE.new_env_name, "ds39")
    self.assertEqual(CE.env_to_clone, "ds310")
    self.assertEqual(CE.new_yml, expected)
    del CE

    # test argv[1]
    CE = envir.CondaEnvir(argv[1])
    self.assertEqual(CE.old_ver, "3.10")



def test_get_export_cmd():
    """
    env_to_clone = 'ds310'
    flag = CondaFlag.HIST
    
    user_dir = DIR_TMP
    yml_file = f"env_{env_to_clone}_{fla.name.lower()}.yml"
    yml_path = proc.path2str(user_dir.joinpath(yml_file))
        
    out = get_export_cmd(env_to_clone, flag, yml_path)
    """
    pass


def test_run_export():
    """
    cmd = test_get_export_cmd()
    run_export(cmd)
    """
    pass
    

def test_create_yamls():
    """
    env_to_clone = 'ds310'
    user_dir = DIR_TMP
    
    new_yamls = create_yamls(env_to_clone, user_dir)
    
    yml_n = get_new_yml_name(env_to_clone, CondaFlag.NOBLD)
    yml_n_path = user_dir.joinpath(yml_n)
    assert new_yamls[0] == yml_n_path
    
    yml_h = get_new_yml_name(env_to_clone, CondaFlag.HIST)
    yml_h_path = user_dir.joinpath(yml_h)
    assert new_yamls[1] == yml_h_path
    """
    pass
    


