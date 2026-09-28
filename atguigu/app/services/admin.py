from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.models.models import AgentRun, AgentToolCall


class AdminService:
    """提供管理员观测 AI Run 的查询能力。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metrics(self) -> dict:
        """返回 AI Run 汇总指标。"""
        agent_runs = await self.session.scalar(
            select(func.count()).select_from(AgentRun)
        )
        average_latency_ms = await self.session.scalar(
            select(func.avg(AgentRun.latency_ms))
        )
        input_tokens = await self.session.scalar(
            select(func.sum(AgentRun.input_tokens))
        )
        output_tokens = await self.session.scalar(
            select(func.sum(AgentRun.output_tokens))
        )
        return {
            "agent_runs": agent_runs,
            "average_latency_ms": average_latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    async def list_runs(self, limit: int) -> list[dict]:
        """返回最近的 AI Run。"""
        runs = (
            await self.session.scalars(
                select(AgentRun)
                .order_by(AgentRun.started_at.desc())
                .limit(limit)
            )
        ).all()
        return [
            {
                "id": run.id,
                "conversation_id": run.conversation_id,
                "state": run.state,
                "model_name": run.model_name,
                "latency_ms": run.latency_ms,
                "input_tokens": run.input_tokens,
                "output_tokens": run.output_tokens
            }
            for run in runs
        ]

    async def get_run(self, run_id: str) -> dict:
        """返回一个 AI Run 及其工具调用记录。"""
        run = await self.session.get(AgentRun, run_id)
        tool_calls = (
            await self.session.scalars(
                select(AgentToolCall)
                .where(AgentToolCall.run_id == run_id)
                .order_by(AgentToolCall.created_at)
            )
        ).all()
        return {
            "run": {
                "id": run.id,
                "state": run.state,
                "prompt_version": run.prompt_version,
                "outcome": run.result,
                "input_tokens": run.input_tokens,
                "output_tokens": run.output_tokens
            },
            "tool_calls": [
                {
                    "tool_call_id": call.tool_call_id,
                    "tool_name": call.tool_name,
                    "arguments": call.arguments,
                    "latency_ms": call.latency_ms
                }
                for call in tool_calls
            ]
        }
