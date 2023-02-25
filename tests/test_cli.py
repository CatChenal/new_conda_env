# test_cli_parser.py

from pathlib import Path
import logging
import pytest
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentError

from new_conda_env import cli


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


def test_cli_main():
        final = Path().home().joinpath("lean_ds39_from_ds310.yml")

        # required args:
        argv = ["-old_ver", "3.10" , "-new_ver", "3.9", "-new_env_name", "ds39", "-env_to_clone", "ds310"]
        cli.main(argv)
        assert final.exists()
