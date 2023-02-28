# test_cli_parser.py

import sys
from pathlib import Path
import logging
import pytest
from unittest import mock
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentError

from new_conda_env import cli, envir


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


def test_parser_wrong():
    
    p = cli.generate_parser()
    
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        p.parse_args(["--old_ver", "-new", "-x"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2


def test_parser_partial():
    
    p = cli.generate_parser()
    
    # partial args
    _cmd = "-old_ver 3.10 -new_ver 3.9 -dotless_ver 1"
    _cmd = _cmd + " -env_to_clone ds310 -new_env_name ds39"

    args = p.parse_args(_cmd.split())
    # check default values:
    assert args.log_level == "ERROR"
    assert args.kernel == "python"


def test_check_ver_num():
    
    msg = "\nATTENTION [Version validation: High version "
    msg = msg + "without period]\n\tIs this version: "
    msg = msg + "'{}' missing a period? Correct and rerun.\n"

    ver = "31"
    err_msg = cli.msgf_high_ver.format(ver)

    with pytest.raises(ValueError) as pytest_wrapped_e:
        cli.check_ver_num(ver)
    assert pytest_wrapped_e.type == ValueError
    assert pytest_wrapped_e.value.args[0] == err_msg

    ver = "31."
    out_ver = cli.check_ver_num(ver)
    assert out_ver == ver

    ver = "3.9.8"
    out_ver = cli.check_ver_num(ver)
    assert out_ver == "3.9"


@mock.patch.object(envir.CondaEnvir, 'get_export_stream')
@mock.patch.object(envir.CondaEnvir, 'get_new_env_yaml')
def test_cli_main(mock_new_yml, mock_get_stream):

    mock_get_stream.return_value = "content"
    argv = ["-old_ver", "3.10" , "-new_ver", "3.9", "-new_env_name", "ds39", "-env_to_clone", "ds310"]
    fname = "lean_ds39_from_ds310.yml"
    mock_new_yml.return_value = fname
    final = Path("tests").joinpath(fname)

    with mock.patch.object(sys, 'argv', argv):
        cli.main(argv)
        assert final.exists()
