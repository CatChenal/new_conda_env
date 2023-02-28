from pathlib import Path
from new_conda_env import processing as proc


def test_path2str():
    some_user_dir = Path.home().joinpath("some_dir")
    to_str_win = proc.path2str(some_user_dir, win_os=True)
    to_str_other = proc.path2str(some_user_dir, win_os=False)
    assert to_str_win == str(to_str_other).replace("/", "\\")
