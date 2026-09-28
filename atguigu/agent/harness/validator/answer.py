from atguigu.agent.harness.errors import AgentOutputValidationError, CorrectableErrorCode

from atguigu.agent.harness.rules.fact import FactChecker
from atguigu.agent.harness.tools.catalog import TOOL_CATALOG, ToolCategory
from atguigu.agent.harness.tools.output import ToolFailureType
from atguigu.agent.harness.tools.snapshot import ToolCallSnapshot
from atguigu.agent.llm.output import AgentOutput, ReplyType


class AnswerValidationError(AgentOutputValidationError):
    """表示 Agent 回复不符合业务事实规则"""


class AnswerValidator:
    """校验 Agent 回复使用的业务数据。"""

    business_failure_message = (
        "暂时无法取得可靠的订单、商品、物流或售后信息，"
        "因此现在不能确认结果，请稍后重试。"
    )

    def __init__(self):
        # 1. 创建业务事实校验器
        self.fact_checker = FactChecker()

    def validate(
            self,
            output: AgentOutput,
            tool_calls: tuple[ToolCallSnapshot, ...]
    ) -> AgentOutput:
        """根据工具执行结果调整回复，并校验最终回复中的业务事实"""

        # 1. 筛选业务工具调用以及其中成功的结果
        business_calls = self._get_business_calls(tool_calls)
        successful_business_calls = self._get_successful_calls(business_calls)

        # 2. 全部业务调用失败时根据失败类型生成安全回复
        if business_calls and not successful_business_calls:
            return self._build_failure_reply(output, business_calls)

        # 3. 使用成功工具结果校验回答中的业务事实
        self._validate_facts(
            output.reply_content,
            successful_business_calls
        )

        # 4. 返回通过失败降级和事实校验的原始输出
        return output

    @staticmethod
    def _get_business_calls(tool_calls: tuple[ToolCallSnapshot, ...]) -> tuple[ToolCallSnapshot, ...]:
        """筛选返回业务数据的工具调用"""

        # 根据工具目录中的类别筛选业务工具
        return tuple(
            tool_call
            for tool_call in tool_calls
            if TOOL_CATALOG.get_tool_category(
                tool_call.tool_name
            ) == ToolCategory.BUSINESS
        )

    @staticmethod
    def _get_successful_calls(business_calls: tuple[ToolCallSnapshot, ...]) -> tuple[ToolCallSnapshot, ...]:
        """筛选可以支持回答事实的成功业务调用"""

        # 保留明确执行成功的业务工具结果
        return tuple(
            tool_call
            for tool_call in business_calls
            if tool_call.success is True
        )

    def _build_failure_reply(
            self,
            output: AgentOutput,
            business_calls: tuple[ToolCallSnapshot, ...]
    ) -> AgentOutput:
        """根据业务、服务调用或契约失败生成安全回复"""

        # 1. 筛选由业务服务明确返回的失败结果
        business_failures = tuple(
            tool_call
            for tool_call in business_calls
            if tool_call.failure_type == ToolFailureType.BUSINESS
        )

        # 2. 全部属于业务失败时使用最后一条业务消息
        if len(business_failures) == len(business_calls):
            latest_failure = business_failures[-1]
            return output.model_copy(
                update={
                    "reply_type": ReplyType.ANSWER,
                    "reply_content": latest_failure.result["message"],
                    "handoff_request": None,
                    "page_action_request": None
                }
            )

        # 3. 存在服务调用或契约失败时返回统一拒绝回复
        return output.model_copy(
            update={
                "reply_type": ReplyType.DECLINE,
                "reply_content": self.business_failure_message,
                "handoff_request": None,
                "page_action_request": None
            }
        )

    def _validate_facts(
            self,
            reply_content: str,
            successful_calls: tuple[ToolCallSnapshot, ...]
    ) -> None:
        """校验最终回复中的业务事实都有成功工具依据"""

        # 1. 查找无法由成功工具参数或结果支持的业务事实
        unsupported_facts = self.fact_checker.get_unsupported_facts(
            reply_content,
            successful_calls
        )

        # 2. 发现无依据事实时返回可供模型纠错的明确错误
        if unsupported_facts:
            values = "、".join(
                fact.value
                for fact in unsupported_facts
            )
            raise AnswerValidationError(
                CorrectableErrorCode.UNSUPPORTED_FACT,
                f"回复中的业务事实缺少工具支持：{values}"
            )
