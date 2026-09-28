from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.agent.harness.tools.snapshot import ToolCallReader
from atguigu.agent.harness.validator.output import AgentOutputValidator
from atguigu.app.repositories.tool import ToolCallRepository
from atguigu.app.services.auth import AuthService
from atguigu.common.config import get_settings
from atguigu.agent.harness.run.coordinator import AgentRunCoordinator
from atguigu.agent.harness.run.executor import AgentExecutor
from atguigu.infrastructure.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service() -> AuthService:
    return AuthService()


def get_tool_call_reader(session: SessionDep) -> ToolCallReader:
    return ToolCallReader(ToolCallRepository(session))


ToolCallReaderDep = Annotated[ToolCallReader,Depends(get_tool_call_reader)]


def get_agent_output_validator(tool_call_reader: ToolCallReaderDep) -> AgentOutputValidator:
    return AgentOutputValidator(tool_call_reader)

AgentOutputValidatorDep = Annotated[AgentOutputValidator,Depends(get_agent_output_validator)]


def get_agent_executor(request: Request,output_validator: AgentOutputValidatorDep) -> AgentExecutor:
    return AgentExecutor(agent=request.app.state.agent, output_validator=output_validator)


AgentExecutorDep = Annotated[AgentExecutor, Depends(get_agent_executor)]


def require_internal_service(token: Annotated[str | None, Header(alias="X-Internal-Service-Token")] = None):
    """只允许 Customer Service 调用内部接口。"""
    if token != get_settings().internal_service_token:
        raise HTTPException(
            status_code=403,
            detail="Invalid internal service token"
        )


def get_agent_coordinator(session: SessionDep,
                          executor: AgentExecutorDep
                          ):
    return AgentRunCoordinator(session=session, executor=executor)


AgentRunCoordinatorDep = Annotated[AgentRunCoordinator, Depends(get_agent_coordinator)]
