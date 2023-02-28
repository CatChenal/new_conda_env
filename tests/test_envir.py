# test_envir.py

import sys
from enum import Enum
from pathlib import Path
import tempfile
import shutil

import pytest
from unittest import mock

from new_conda_env import envir, processing as proc

#.........................................................

class CondaFlag(Enum):
    NOBLD = "--no-builds"
    HIST = "--from-history"
    
DIR_TMP = Path().home()

"""
@pytest.fixture(scope="module")
def my_filepath(self):
    tmpdir = tempfile.mkdtemp()
    subdir = Path(tmpdir).joinpath("test_envir")
    subdir.mkdir(parents=True, exist_ok=True)
    
    yield subdir.joinpath("lean.yml")
    shutil.rmtree(tmpdir)
"""


"""Need to patch class CondaEnvir to test its methods
"""


"""
@pytest.mark.parametrize(
    "test_input,expected",
    [("3+5", 8), ("2+4", 6), pytest.param("6*9", 42, marks=pytest.mark.xfail)],
)
def test_eval(test_input, expected):
    assert eval(test_input) == expected


class MyTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def initdir(self, tmpdir):
        tmpdir.chdir()  # change to pytest-provided temporary directory
        tmpdir.join("samplefile.ini").write("# testdata")

    def test_method(self):
        with open("samplefile.ini") as f:
            s = f.read()
        assert "testdata" in s
"""

#CONTENT = "content"


#excluded = ["get_export_stream","get_new_env_yaml",
#            "get_rc_python_deps","has_user_rc","get_user_rc","user_rc"]
#@pytest.mark.parametrize("argv", [dict_ok, pytest.param(dict_fail, 
#                                                        marks=pytest.mark.xfail)])
@mock.patch.object(envir.CondaEnvir, 'get_export_stream')
@mock.patch.object(envir.CondaEnvir, 'get_new_env_yaml')
def test_CondaEnvir(mock_new_yml, mock_get_stream):
    #kwargs_req_expect = ["3.10" ,  "39", "ds310"]

    #prep:
    kwargs_all = ["old_ver", "new_ver", "env_to_clone"] \
        + ["dotless_ver", "new_env_name", "kernel", "display_new_yml", "log_level"]
    kwargs_req_vals = ["3.10" ,  "3.9", "ds310"]
    kwagrs_opts_def_vals = [1, "default", "Python", 1, "ERROR"]
    kwagrs_opts_fail_vals = [1, "default", "R", 1, "ERROR"]

    kwargs_vals = kwargs_req_vals + kwagrs_opts_def_vals
    kwagrs_vals_fail_opts = kwargs_req_vals + kwagrs_opts_fail_vals

    dict_ok = dict(zip(kwargs_all, kwargs_vals))
    dict_fail = dict(zip(kwargs_all, kwagrs_vals_fail_opts))

    # test 1
    CE = envir.CondaEnvir(**dict_ok)
    mock_get_stream.return_value = "content" #CONTENT
    lean_expected = f"lean_{CE.new_env_name}_from_{CE.env_to_clone}.yml"
    mock_new_yml.return_value = lean_expected

    assert CE.old_ver, dict_ok["old_ver"]
    assert CE.kernel, dict_ok["kernel"].lower()

    # default new env name
    fstr = "env{}{}"
    
    new_env_name = fstr.format(dict_ok["kernel"].lower()[:2],
                               dict_ok["new_ver"].replace(".",""))
    assert CE.new_env_name, new_env_name

    assert CE.env_to_clone, dict_ok["env_to_clone"]
    assert CE.new_yml, lean_expected

    # test get_export_cmd
    flag = CondaFlag.HIST
    cmd = "conda env export -n {} {}"
    export_cmd = cmd.format(dict_ok["env_to_clone"], flag)
    assert CE.get_export_cmd(dict_ok["env_to_clone"], flag) == export_cmd

    # test get_lean_yml_pathname
    user_dir = Path().home()
    from_env = dict_ok["env_to_clone"].replace('.','')
    n = f"lean_{new_env_name}_from_{from_env}.yml" 
    yml_file = user_dir.joinpath(n)
    assert CE.get_lean_yml_pathname() == yml_file
    
    del CE

    # test fail
    CE = envir.CondaEnvir(**dict_fail)
    assert ValueError

    


