from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy.utils.defer import deferred_from_coro

from gzspidertools.common.expend import PostgreSQLPipeEnhanceMixin
from gzspidertools.common.multiplexing import ReuseOperation
from gzspidertools.common.sqlformat import GenPostgresqlAsyncpg
from gzspidertools.common.typevars import PortalTag
from gzspidertools.exceptions import NotConfigured
from gzspidertools.utils.database import PostgreSQLAsyncPortal

try:
    from asyncpg.pool import Pool as PGPool  # noqa: TC002
except ImportError:
    raise NotConfigured(
        "missing psycopg_pool library, please install it. "
        "install command: pip install gzspidertools[database]"
    )

__all__ = [
    "AyuAsyncPostgresPipeline",
]

if TYPE_CHECKING:
    from twisted.internet.defer import Deferred

    from gzspidertools.spiders import AyuSpider


class AyuAsyncPostgresPipeline(PostgreSQLPipeEnhanceMixin):
    pool: PGPool

    def open_spider(self, spider: AyuSpider) -> Deferred:
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息！"
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider: AyuSpider) -> None:
        self.pool = await PostgreSQLAsyncPortal(
            db_conf=spider.postgres_conf, tag=PortalTag.LIBRARY
        ).connect()

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            alter_item = ReuseOperation.reshape_item(item_dict)
            sql, args = GenPostgresqlAsyncpg.upsert_generate(
                db_table=alter_item.table.name,
                conflict_cols=alter_item.conflict_cols,
                data=alter_item.new_item,
                update_cols=alter_item.update_keys,
            )
            await conn.execute(sql, *args)

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await self.insert_item(item_dict)
        return item

    async def _close_spider(self) -> None:
        await self.pool.close()

    def close_spider(self, spider: AyuSpider) -> Deferred:
        return deferred_from_coro(self._close_spider())
