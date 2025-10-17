from __future__ import annotations

from typing import TYPE_CHECKING

from pyutilkit.term import SGRString

from pvenv.subcommands.base import BaseCommand

if TYPE_CHECKING:
    from argparse import Namespace


class Command(BaseCommand):
    __slots__ = ()

    def __init__(self, options: Namespace) -> None:
        super().__init__(options)

    def run(self) -> None:
        for directory in sorted(self.base_dir.glob("*")):
            if directory.is_dir():
                SGRString(directory.name).print()
