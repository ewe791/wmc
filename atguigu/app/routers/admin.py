from typing import Annotated

from fastapi import APIRouter, Header

from atguigu.app.dependencies import SessionDep, get_auth_service
from atguigu.app.services.admin import AdminService

router = APIRouter(prefix="/api/v1", tags=["AI Operations"])


@router.get("/admin/metrics")
async def get_admin_metrics(
        session: SessionDep,
        authorization: Annotated[str | None, Header()] = None
) -> dict:
    """返回管理员观测面板使用的 AI Run 汇总指标。"""
    get_auth_service().get_authorized_user(
        authorization,
        "admin"
    )
    return await AdminService(session).get_metrics()


@router.get("/runs")
async def list_runs(
        session: SessionDep,
        limit: int = 50,
        authorization: Annotated[str | None, Header()] = None
) -> list[dict]:
    """返回最近的 AI Run。"""
    get_auth_service().get_authorized_user(
        authorization,
        "admin"
    )
    return await AdminService(session).list_runs(limit)


@router.get("/runs/{run_id}")
async def get_run(
        run_id: str,
        session: SessionDep,
        authorization: Annotated[str | None, Header()] = None
) -> dict:
    """返回一个 AI Run 及其工具调用记录。"""
    get_auth_service().get_authorized_user(
        authorization,
        "admin"
    )
    return await AdminService(session).get_run(run_id)
