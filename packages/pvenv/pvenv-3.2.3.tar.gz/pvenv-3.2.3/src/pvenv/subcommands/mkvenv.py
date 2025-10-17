from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from uv import find_uv_bin

from pvenv.subcommands.base import BaseCommand

if TYPE_CHECKING:
    from argparse import Namespace

DEV_NULL = Path(os.devnull)


class Command(BaseCommand):
    __slots__ = ("environments", "legacy_seed", "project", "python", "seed", "venv")

    def __init__(self, options: Namespace) -> None:
        super().__init__(options)
        self.venv: str = options.venv
        self.python: str = options.python
        self.legacy_seed: bool = options.legacy_seed
        self.seed: bool = options.seed
        self.project: Path = Path(options.project).absolute()
        self.environments: list[Path] = self._get_environments(options.environments)

    def _get_environments(self, environments: list[str]) -> list[Path]:
        if self.project == DEV_NULL and environments:
            msg = "Cannot set environ in independent"
            raise RuntimeError(msg)
        return [self.project.joinpath(environ) for environ in environments]

    def run(self) -> None:
        venv_path = self.base_dir.joinpath(self.venv)
        if venv_path.exists():
            msg = f"Venv {self.venv} already exists, aborting..."
            raise RuntimeError(msg)

        uv_path = find_uv_bin()

        if not self.python:
            self.execute(f"mkdir -p {venv_path}")
        else:
            extra_args = []
            if self.python != "system":
                extra_args.append(f"--python {self.python}")
            if self.legacy_seed:
                extra_args.append("--seed")
            extra = " ".join(extra_args)
            self.execute(f"{uv_path} venv --relocatable {extra} {venv_path}")
            self.execute(f"echo {self.python} > {venv_path}/.python")

        if self.project != DEV_NULL:
            self.execute(f"echo {self.project} > {venv_path}/.project")

        for i, environment in enumerate(self.environments):
            if i == 0:
                self.execute(f": > {venv_path}/.environment")
            self.execute(f"echo {environment} >> {venv_path}/.environment")

        self.execute(f"avenv {self.venv}")

        if self.seed:
            self.execute(f"{uv_path} pip install --upgrade uv")
