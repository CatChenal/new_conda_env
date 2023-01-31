import os
from pathlib import Path
import subprocess
from subprocess import Popen, PIPE

from yaml import Loader, Dumper


def get_python_dirs():
    """Run the command `where python` in the current directory.
    """
    with Popen(["where", "python"], stdout=PIPE, text=True) as proc:
        python_dirs = proc.stdout.read()
        
    return python_dirs


def get_user_dirs(dirs: list[str]):
    """Return the directories with Users|home from a list of directories.
    p = PurePath('/usr/bin/python3')
    p.parts
    ('/', 'usr', 'bin', 'python3') #linux

    p = PureWindowsPath('c:/Program Files/PSF')
    p.parts
    ('c:\\', 'Program Files', 'PSF')
    """
    
    return [d in dirs if Path(d).home.__contains("Users")]



def get_envir_yml():
    """data = load(stream, Loader=Loader)
    """
    
    return
    
def main():
    python_dirs = get_python_dirs().split('\n')
    user_dirs = get_user_dirs(python_dirs)
    
    
    
# Windows 10 with Anaconda3 and username “jsmith”– C:\Users\jsmith\Anaconda3\python.exe.
# In a conda environment called “my-env” might be in a location such as C:\Users\jsmith\Anaconda3\envs\my-env\python.exe

if __name__ == "__main__":
    user_dir = main()
    print(f"user_dir type: {type(user_dir)}")
    print(f"User python dir:\n{user_dir}")
