# test_cli_parser.py

import sys
import logging
import pytest
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentError
from new_conda_env.cli import generate_parser, check_ver_num


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


def test_parser_wrong():
    
    p = generate_parser()
    
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        p.parse_args(["-old", "-new", "-x"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2


def test_parser_partial():
    
    p = generate_parser()
    
    # partial args
    _cmd = "-old_ver 3.10 -new_ver 3.9 -dotless_ver 1"
    _cmd = _cmd + " -env_to_clone ds310 -new_env_name ds39"

    args = p.parse_args(_cmd.split())
    assert args.log_level == "ERROR"
    assert args.kernel == "python"


def test_check_ver_num():
    
    msg = "\nATTENTION [Version validation: High version "
    msg = msg + "without period]\n\tIs this version: "
    msg = msg + "'{}' missing a period? Correct and rerun.\n"

    ver = "31"
    with pytest.raises(ValueError) as pytest_wrapped_e:
        check_ver_num(ver)
    assert pytest_wrapped_e.type == ValueError
    assert pytest_wrapped_e.value.args[0] == msg.format(ver)

    ver = "31."
    out_ver = check_ver_num(ver)
    assert out_ver == ver

    ver = "3.9.8"
    out_ver = check_ver_num(ver)
    assert out_ver == "3.9"


