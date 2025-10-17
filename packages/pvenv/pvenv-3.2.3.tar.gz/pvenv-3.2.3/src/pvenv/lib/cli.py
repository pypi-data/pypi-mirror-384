import os
import sys
from argparse import SUPPRESS, ArgumentParser, BooleanOptionalAction, Namespace
from pathlib import Path

from pvenv.__version__ import __version__

sys.tracebacklimit = 0


def get_default_base() -> Path:
    default = "~/.local/share/virtualenvs"
    return Path(os.getenv("PVENV_BASE", default)).expanduser().absolute()


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog="pvenv",
        description="A utility to manage virtual environments",
        epilog="You can find the full documentation at: https://p-venv.readthedocs.io/en/stable/",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="print the version and exit",
    )

    default_base = get_default_base()
    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--base_dir",
        action="store_const",
        const=default_base,
        default=default_base,
        help=SUPPRESS,
    )
    parent_parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="only print the commands to be executed",
    )
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="increase the level of verbosity",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparsers.add_parser("out", help="List venvs", parents=[parent_parser])
    subparsers.add_parser("list", help="List venvs", parents=[parent_parser])
    subparsers.add_parser(
        "init", help="Initialisation instructions for pvenv", parents=[parent_parser]
    )
    subparsers.add_parser(
        "deactivate", help="Deactivate a venv", parents=[parent_parser]
    )

    invenv_parser = subparsers.add_parser(
        "in", help="Export new variables for the venv", parents=[parent_parser]
    )
    invenv_parser.add_argument("env_vars", nargs="*")
    invenv_parser.add_argument("-f", "--files", action="append", default=[])

    avenv_parser = subparsers.add_parser(
        "activate", help="Activate a venv", parents=[parent_parser]
    )
    avenv_parser.add_argument("venv")
    avenv_parser.add_argument("-n", "--no-cd", dest="cd", action="store_false")

    mkvenv_parser = subparsers.add_parser(
        "make", help="Make a new venv", parents=[parent_parser]
    )
    mkvenv_parser.add_argument("venv", nargs="?", default=Path().absolute().name)
    mkvenv_parser.add_argument("-e", "--environments", action="append", default=[])
    mkvenv_parser.add_argument("-P", "--project", default=Path().absolute().as_posix())
    mkvenv_parser.add_argument("-p", "--python", default="system")
    mkvenv_parser.add_argument("--legacy-seed", action=BooleanOptionalAction)
    mkvenv_parser.add_argument("--seed", action=BooleanOptionalAction)

    rmvenv_parser = subparsers.add_parser(
        "rm", help="Remove virtualenvs", parents=[parent_parser]
    )
    rmvenv_parser.add_argument("venvs_to_remove", nargs="*")

    args = parser.parse_args()
    if args.verbosity > 0:
        sys.tracebacklimit = 1000

    return args
