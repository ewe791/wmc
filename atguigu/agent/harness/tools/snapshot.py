from dataclasses import dataclass
from typing import Any

from atguigu.agent.harness.tools.output import ToolFailureType
from atguigu.app.repositories.tool import ToolCallRepository
from atguigu.models.models import AgentToolCall


@dataclass(frozen=True)
class ToolCallSnapshot:
    """保存一次工具调用用于后续校验的只读快照"""

    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    success: bool | None
    failure_type: ToolFailureType | None = None

    @classmethod
    def from_tool_call(cls, tool_call: AgentToolCall) -> "ToolCallSnapshot":
        """从数据库工具调用记录创建只读快照"""

        # 1. 复制调用参数和结果，避免校验过程修改 ORM 数据
        return cls(
            tool_name=tool_call.tool_name,
            arguments=dict(tool_call.arguments),
            result=dict(tool_call.result) if tool_call.result is not None else None,
            success=tool_call.success,
            #  2. 将持久化的失败分类恢复成枚举值
            failure_type=(
                ToolFailureType(tool_call.result["failure_type"])
                if (
                        tool_call.result is not None
                        and tool_call.result.get("failure_type") is not None
                )
                else None
            )
        )


class ToolCallReader:
    """按 Agent Run 读取工具调用快照。"""

    def __init__(self, repository: ToolCallRepository):
        # 1. 保存读取工具调用记录的仓储
        self.repository = repository

    async def read_by_run_id(
            self,
            run_id: str
    ) -> tuple[ToolCallSnapshot, ...]:
        """返回一次 Agent Run 的全部工具调用快照。"""

        # 1. 按创建顺序读取当前 Run 的工具调用记录
        tool_calls = await self.repository.list_by_run_id(run_id)

        # 2. 将 ORM 记录转换成校验器使用的只读快照
        return tuple(ToolCallSnapshot.from_tool_call(tool_call) for tool_call in tool_calls)
