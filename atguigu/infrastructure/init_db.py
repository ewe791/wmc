from atguigu.common.event_loop import run_async
from atguigu.infrastructure.db import db_engine
from atguigu.models.models import Base


async def init_database() -> None:
    """创建 AI Service 声明的数据库表和索引。"""
    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    run_async(init_database())
