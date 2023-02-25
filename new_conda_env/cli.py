# cli.py
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
#logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)
sh = logging.StreamHandler()
formatter = logging.Formatter('%(name)-15s: %(levelname)-8s %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)
log.setLevel(logging.ERROR)


# msgf_ :: message string requiering add'l .format() fn
msgf_high_ver = """
ATTENTION [Version validation: High version without period]
    Is this version: '{}' missing a period?
    Correct and rerun.
"""


def generate_parser():
    
    p = ArgumentParser(prog="new_conda_env",
        description = __doc__,
        formatter_class = ArgumentDefaultsHelpFormatter,
        exit_on_error = True
    )
    p.add_argument(
        "-old_ver", nargs=1, type=str, required=True,
        help="""The kernel (python) version of an existing env to 'clone'. 
        For example, 3.8 but not 38 (python kernel)."""
    )
    p.add_argument(
        "-new_ver", nargs=1, type=str, required=True,
        help="""The kernel (python) version of the new env. 
        For example, 3.8 but not 38 (python kernel)."""
    )
    p.add_argument(
        "-dotless_ver", nargs=1, choices=[1,0],
        default=1, type=bool,
        help="Whether to remove any dot in the final yml (default) filename."
    )
    p.add_argument(
        "-env_to_clone", nargs=1, type=str, required=True,
        help="Name of an existing env to 'clone'."
    )
    p.add_argument(
        "-new_env_name", nargs=1, type=str,
        default="default",
        help="""Optional: name for the new env yml file else default pattern used:
          Pattern: 'env' + self.new_ver, e.g. env3.11 or env311"""
    ) 
    p.add_argument(
        "-kernel", nargs=1, choices=["python"], type=str,
        default="python",
        help="Optional: 'python' is the default (and only kernel so far implemented)."
    )
    p.add_argument(
        "-display_new_yml", nargs=1, choices=[1,0],
        default=1, type=bool,
        help="Wether to display the contents of the new yaml file."
    )
    level_choices = list(logging._nameToLevel.keys())
    p.add_argument(
        "-log_level", nargs=1, choices=level_choices,
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
            msg = msgf_high_ver.format(ver)
            log.error(msg)
            raise ValueError(msg)
            
    if dots >= 2:
        ver = ver[:-ver.find(pt,1)-1]
        log.info("Version truncated to <major.minor>.")
    return ver


def check_kernel(kernel: str) -> None:
    if kernel != "python":
        log.error("Post an enhancement issue!")
        raise NotImplementedError("Post an enhancement issue!")
    return kernel


def main(argv=None):
    
    conda_env_parser = generate_parser()
    
    args = conda_env_parser.parse_args(argv)
    args = args or ["--help"]

    log.setLevel(args.log_level)

    # validation before instanciation
    o_ver = check_ver_num(args.old_ver) 
    n_ver = check_ver_num(args.new_ver)
    check_kernel(args.kernel)
    
    # won't reach this stage if any step in validation fails
    conda_vir = envir.CondaEnvir(old_ver=o_ver,
                                 new_ver=n_ver, 
                                 dotless_ver=args.dotless_ver,
                                 env_to_clone=args.env_to_clone,
                                 new_env_name=args.new_env_name,
                                 kernel=args.kernel,
                                 display_new_yml=args.display_new_yml,
                                 log_level=args.log_level)
            
    conda_vir.create_new_env_yaml()

    return 0
    

if __name__ == "__main__":

    sys.exit(main(sys.argv))
