from __future__ import annotations

from typing import TYPE_CHECKING

from pyutilkit.term import SGRString

from pvenv.lib.constants import SHELL_PREFIX

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path


class BaseCommand:
    __slots__ = ("base_dir", "dry_run", "verbosity")

    def __init__(self, options: Namespace) -> None:
        self.base_dir: Path = options.base_dir
        self.dry_run: bool = options.dry_run
        self.verbosity: int = options.verbosity

    def run(self) -> None:
        raise NotImplementedError

    def execute(self, command: str) -> None:
        if self.verbosity or self.dry_run:
            SGRString(command).print()

        if not self.dry_run:
            SGRString(command, prefix=SHELL_PREFIX, force_prefix=True).print()
