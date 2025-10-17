from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pyutilkit.term import SGRString

from pvenv.subcommands.base import BaseCommand

if TYPE_CHECKING:
    from argparse import Namespace


class Command(BaseCommand):
    __slots__ = ()

    def __init__(self, options: Namespace) -> None:
        super().__init__(options)

    @staticmethod
    def shell_script() -> Path:
        return Path(__file__).parents[1].joinpath("scripts/pvenv.sh").resolve()

    def run(self) -> None:
        SGRString("Add the following line to your shell rc:").print()
        SGRString(f". {self.shell_script()}").print()
