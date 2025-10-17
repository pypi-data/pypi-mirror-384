from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pvenv.subcommands.base import BaseCommand

if TYPE_CHECKING:
    from argparse import Namespace


class Command(BaseCommand):
    __slots__ = ()

    def __init__(self, options: Namespace) -> None:
        super().__init__(options)

    def run(self) -> None:
        self.execute(f"declare -f deactivate > {os.devnull} && deactivate")
        self.execute("outvenv")
