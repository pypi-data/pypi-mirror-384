from pathlib import Path

from scrapy.commands.genspider import Command

import gzspidertools


class AyuCommand(Command):
    @property
    def templates_dir(self) -> str:
        return str(
            Path(
                Path(gzspidertools.__path__[0], "templates"),
                "spiders",
            )
        )
