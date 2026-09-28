import json
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from atguigu.common.config import get_settings

db_engine = create_async_engine(
    get_settings().ai_database_url,
    echo=False,
    json_serializer=lambda value: json.dumps(
        value,
        ensure_ascii=False
    )
)
session_factory = async_sessionmaker(
    db_engine,
    expire_on_commit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """为一次请求提供数据库 Session。"""
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
