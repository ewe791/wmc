import asyncio
import selectors
from collections.abc import Coroutine


def create_selector_event_loop() -> asyncio.AbstractEventLoop:
    """创建 Psycopg 异步连接兼容的 Selector 事件循环。"""
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


def run_async[ResultT](coro: Coroutine) -> ResultT:
    """使用 Selector 事件循环运行协程。"""
    return asyncio.run(
        coro,
        loop_factory=create_selector_event_loop
    )
