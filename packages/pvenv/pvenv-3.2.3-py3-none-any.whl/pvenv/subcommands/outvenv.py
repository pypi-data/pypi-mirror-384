from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pvenv.lib.constants import ENV_VAR_PREFIX, UNSET_ID
from pvenv.subcommands.base import BaseCommand

if TYPE_CHECKING:
    from argparse import Namespace


class Command(BaseCommand):
    __slots__ = ()

    def __init__(self, options: Namespace) -> None:
        super().__init__(options)

    def run(self) -> None:
        if ENV_VAR_PREFIX not in os.environ:
            return

        self.execute(f"unset {ENV_VAR_PREFIX}")
        prefix_size = len(ENV_VAR_PREFIX) + 1
        unset_prefix_size = len(ENV_VAR_PREFIX) + len(UNSET_ID) + 2
        for key, value in os.environ.items():
            if key.startswith(f"{ENV_VAR_PREFIX}_"):
                if key.startswith(f"{ENV_VAR_PREFIX}_{UNSET_ID}_"):
                    self.execute(f"unset {key[unset_prefix_size:]}")
                else:
                    self.execute(f"export {key[prefix_size:]}={value}")
                self.execute(f"unset {key}")
