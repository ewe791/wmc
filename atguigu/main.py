import uvicorn

from atguigu.common.config import get_settings
from atguigu.common.event_loop import run_async


async def serve() -> None:
    settings = get_settings()
    server = uvicorn.Server(
        uvicorn.Config(
            "atguigu.app.app:app",
            host=settings.api_host,
            port=settings.api_port,
            loop="none"
        )
    )
    await server.serve()


if __name__ == "__main__":
    run_async(serve())
