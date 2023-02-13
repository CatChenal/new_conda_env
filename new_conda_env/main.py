# cli.py
__doc__ = """
conda_new_env is a tool for creating a 'lean' environment from
an existing one, e.g. when a new kernel version is desired.
"""
import sys
from logging import getLogger
from new_conda_env import envir
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
# ..........................................................................

log = getLogger(__name__)


def generate_parser():
    
    p = ArgumentParser(prog="new_conda_env",
        description = __doc__,
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    p.add_argument(
        "-old_ver", nargs='?', type=str,
        help="The kernel (python) version of an existing env to 'clone'."
    )
    p.add_argument(
        "-new_ver", nargs='?', type=str,
        help="The kernel (python) version of the new env"
    )
    p.add_argument(
        "-dotless_ver", nargs='?', choices=[1,0],
        default=1, type=bool,
        help="Whether to remove any dor in new_env"
    )
    p.add_argument(
        "-env_to_clone", nargs='?', type=str,
        help="Name of an existing env to 'clone'."
    )
    p.add_argument(
        "-new_env_name", nargs='?', type=str,
        default="default",
        help="""Optional: name for the new env; default pattern used if omitted:
        Pattern: 'env' + self.new_ver, e.g. env3.11 or env311"""
    ) 
    p.add_argument(
        "-kernel", nargs='?', choices=["python"], type=str,
        default="python",
        help="Optional: 'python' is the default (and only kernel so far implemented)."
    )
    p.add_argument(
        "-display_new_yml", nargs='?', choices=[1,0],
        default=1, type=bool,
        help="Wether to display the contents of the new yaml file."
    )
    p.add_argument(
        "-debug", nargs='?', choices=[1,0],
        default=1, type=bool,
        help="Optional: log with debug mode."
    )
    
    return p


def check_ver_num(ver):
    """Truncate micro version number to return major.minor only.
    (This helps conda with satisfiability.)
    """
    pt = '.'
    if ver.count(pt) == 2:
        ver = ver[:-ver.find(pt,1)-1]
        log.info("Version truncated to major.minor.")
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
                                 debug=args.debug)

    conda_vir.create_new_env_yaml()
    

if __name__ == "__main__":
    sys.exit(main())