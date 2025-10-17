from gzspidertools.common.typevars import PortalTag
from gzspidertools.config import logger
from gzspidertools.items import AyuItem
from gzspidertools.scraper.http.request.aiohttp import AiohttpRequest
from gzspidertools.scraper.spiders import AyuSpider
from gzspidertools.scraper.spiders.crawl import AyuCrawlSpider

__all__ = [
    "AiohttpRequest",
    "AyuCrawlSpider",
    "AyuItem",
    "AyuSpider",
    "PortalTag",
    "__version__",
    "logger",
]

__version__ = "0.0.30"
