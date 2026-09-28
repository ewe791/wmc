from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from atguigu.app.routers import admin, run
from atguigu.agent.factory import create_support_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    调用时机：应用启动前、应用关闭前
    """
    # 初始化资源动作
    app.state.agent = create_support_agent()

    yield  # 处理路由请求的分界线

    # 释放资源的动作（数据库的资源、后台任务、中间件的资源redis）


app = FastAPI(title="Ecommerce AI Service", lifespan=lifespan)
app.include_router(run.router)
app.include_router(admin.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
