from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.models.models import AgentToolCall


class ToolCallRepository:
    """封装 AgentToolCall 的持久化操作"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, tool_call: AgentToolCall):
        self.session.add(tool_call)

    async def find_by_run_and_call_id(
            self,
            run_id: str,
            tool_call_id: str
    ) -> AgentToolCall:
        statement = select(AgentToolCall).where(
            AgentToolCall.run_id == run_id,
            AgentToolCall.tool_call_id == tool_call_id
        )
        return await self.session.scalar(statement)

    async def list_by_run_id(self,run_id: str) -> list[AgentToolCall]:

        # 1. 构建当前运行全部工具调用的查询
        statement = (
            select(AgentToolCall)
            .where(AgentToolCall.run_id == run_id)
            .order_by(AgentToolCall.created_at)
        )
        # 2. 执行查询
        result = await self.session.scalars(statement)

        # 3. 转换成调用方可以直接使用的列表
        return list(result)
