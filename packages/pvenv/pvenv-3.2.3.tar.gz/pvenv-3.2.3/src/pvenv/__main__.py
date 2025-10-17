from typing import TYPE_CHECKING

from pvenv import subcommands
from pvenv.lib.cli import parse_args

if TYPE_CHECKING:
    from types import ModuleType


def main() -> None:
    args = parse_args()
    module: ModuleType
    if args.subcommand == "in":
        module = subcommands.invenv
    elif args.subcommand == "init":
        module = subcommands.initvenv
    elif args.subcommand == "out":
        module = subcommands.outvenv
    elif args.subcommand == "activate":
        module = subcommands.avenv
    elif args.subcommand == "deactivate":
        module = subcommands.dvenv
    elif args.subcommand == "list":
        module = subcommands.lsvenv
    elif args.subcommand == "make":
        module = subcommands.mkvenv
    elif args.subcommand == "rm":  # pragma: no branch
        module = subcommands.rmvenv
    module.Command(args).run()
