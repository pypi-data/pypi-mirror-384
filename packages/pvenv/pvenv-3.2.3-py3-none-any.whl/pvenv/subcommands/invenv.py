from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from pvenv.lib.constants import ENV_VAR_PREFIX, UNSET_ID
from pvenv.subcommands.base import BaseCommand

if TYPE_CHECKING:
    from argparse import Namespace


class Command(BaseCommand):
    __slots__ = ("env_vars", "files")

    def __init__(self, options: Namespace) -> None:
        super().__init__(options)
        self.env_vars: list[str] = options.env_vars
        self.files: list[Path] = [Path(file).resolve() for file in options.files]

    @staticmethod
    def parse_env_var(line: str) -> list[str]:
        return line.split("=", maxsplit=1)

    def run(self) -> None:
        if ENV_VAR_PREFIX in os.environ:
            msg = "Already in a venv, aborting..."
            raise RuntimeError(msg)

        new_vars = {}
        for file in self.files:
            with file.open() as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if line and not line.startswith("#"):
                        key, value = self.parse_env_var(line)
                        new_vars[key] = value
        for env_var in self.env_vars:
            key, value = self.parse_env_var(env_var)
            new_vars[key] = value

        if new_vars:
            self.execute(f"export {ENV_VAR_PREFIX}=true")
        for key, value in new_vars.items():
            if key in os.environ:
                self.execute(f"export {ENV_VAR_PREFIX}_{key}={os.getenv(key, '')}")
            else:
                self.execute(f"export {ENV_VAR_PREFIX}_{UNSET_ID}_{key}=")
            self.execute(f"export {key}={value}")
