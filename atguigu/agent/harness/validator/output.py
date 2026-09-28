from pydantic import Field

from atguigu.agent.harness.rules.action import PageAction
from atguigu.agent.harness.tools.snapshot import ToolCallReader
from atguigu.agent.harness.validator.action import PageActionValidator
from atguigu.agent.harness.validator.answer import AnswerValidator
from atguigu.agent.llm.output import AgentOutput


class ValidatedAgentOutput(AgentOutput):
    page_action: PageAction | None = None
    token_usage: dict[str, int] = Field(
        default_factory=lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
        }
    )


class AgentOutputValidator:

    def __init__(self, tool_call_reader: ToolCallReader):
        # 1. 保存读取当前 Run 工具证据的组件
        self.tool_call_reader = tool_call_reader

        # 2. 创建回答事实和页面动作校验器
        self.answer_validator = AnswerValidator()
        self.page_action_validator = PageActionValidator()

    async def validate(self, agent_output: AgentOutput, run_id: str) -> ValidatedAgentOutput:
        """校验回答和页面动作并返回可信输出"""

        # 1. 读取当前 Run 已持久化的全部工具调用快照
        tool_calls = await self.tool_call_reader.read_by_run_id(run_id)

        # 2. 校验回答中的失败降级规则和业务事实
        checked_answer_output = self.answer_validator.validate(agent_output, tool_calls)

        # 3. 校验页面动作并由服务端生成可信跳转信息
        page_action = self.page_action_validator.validate(
            checked_answer_output.page_action_request,
            tool_calls
        )
        # 4. 合并模型回复和服务端生成的可信页面动作
        return ValidatedAgentOutput.model_validate(
            {
                **checked_answer_output.model_dump(),
                "page_action": page_action
            }
        )
