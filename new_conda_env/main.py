# main.py
__doc__ = """Main module (cli):
conda_new_env is a tool for 'lean cloning' an environment from 
an existing one, e.g. when a new kernel version is desired. 
The output is a yml file without dependencies versions except for that 
of the (python) kernel and includes any pip dependencies."
"""
import sys
import logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from new_conda_env import envir
# ..........................................................................

log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)


def generate_parser():
    
    p = ArgumentParser(prog="new_conda_env",
        description = __doc__,
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    p.add_argument(
        "-old_ver", nargs="?", type=str,
        help="""The kernel (python) version of an existing env to 'clone'. 
        For example, 3.8 but not 38 (python kernel)."""
    )
    p.add_argument(
        "-new_ver", nargs="?", type=str,
        help="""The kernel (python) version of the new env. 
        For example, 3.8 but not 38 (python kernel)."""
    )
    p.add_argument(
        "-dotless_ver", nargs="?", choices=[1,0],
        default=1, type=bool,
        help="Whether to remove any dot in the final yml (default) filename."
    )
    p.add_argument(
        "-env_to_clone", nargs="?", type=str,
        help="Name of an existing env to 'clone'."
    )
    p.add_argument(
        "-new_env_name", nargs="?", type=str,
        default="default",
        help="""Optional: name for the new env yml file else default pattern used:
          Pattern: 'env' + self.new_ver, e.g. env3.11 or env311"""
    ) 
    p.add_argument(
        "-kernel", nargs="?", choices=["python"], type=str,
        default="python",
        help="Optional: 'python' is the default (and only kernel so far implemented)."
    )
    p.add_argument(
        "-display_new_yml", nargs="?", choices=[1,0],
        default=1, type=bool,
        help="Wether to display the contents of the new yaml file."
    )
    level_choices = list(logging._nameToLevel.keys())
    p.add_argument(
        "-log_level", nargs="?", choices=level_choices,
        default="ERROR", type=str,
        help="Optional: log with debug mode."
    )
    
    return p


def check_ver_num(ver: str) -> str:
    """Truncate micro version number to return major.minor only.
    (This helps conda with satisfiability.)
    Alert user if ver has 2+ digits but no period:
    This could be a misunderstanding of the dotless_ver param.
    """
    pt = '.'
    dots = ver.count(pt)
    if not dots:
        if len(ver) > 1:
            msg = "\nATTENTION [Version validation: High version "
            msg = msg + "without period]\n\tIs this version: "
            msg = msg + f"'{ver}' missing a period? Correct and rerun.\n"
            log.error(msg)
            raise ValueError(msg)
            
    if dots >= 2:
        ver = ver[:-ver.find(pt,1)-1]
        log.info("Version truncated to <major.minor>.")
    return ver


def main():
    
    conda_env_parser = generate_parser()
    
    args = conda_env_parser.parse_args()
    args = args or ["--help"]

    conda_vir = envir.CondaEnvir(old_ver=check_ver_num(args.old_ver),
                                 new_ver=check_ver_num(args.new_ver), 
                                 dotless_ver=args.dotless_ver,
                                 env_to_clone=args.env_to_clone,
                                 new_env_name=args.new_env_name,
                                 kernel=args.kernel,
                                 display_new_yml=args.display_new_yml,
                                 log_level=args.log_level)
            
    conda_vir.create_new_env_yaml()
    

if __name__ == "__main__":
    sys.exit(main())