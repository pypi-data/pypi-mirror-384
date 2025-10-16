from __future__ import annotations

from typing import TYPE_CHECKING

from scrapy.commands.version import Command

from gzspidertools import __version__

if TYPE_CHECKING:
    import argparse


class AyuCommand(Command):
    def short_desc(self) -> str:
        return "Print gzspidertools version"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        print(f"gzspidertools {__version__}")
