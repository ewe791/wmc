from typing import Any, Final

from langchain.agents.middleware.tool_call_limit import ToolCallLimitExceededError
from langchain_core.callbacks import UsageMetadataCallbackHandler
from pydantic import ValidationError

from atguigu.agent.harness.errors import AgentExecutionError, AgentOutputValidationError, TerminalErrorCode, \
    CorrectableErrorCode
from atguigu.agent.harness.rules.correction import OutputCorrectionRules
from atguigu.agent.harness.run.runtime import AgentRuntimeContext
from atguigu.agent.llm.adapter import ModelAdapter
from atguigu.agent.llm.output import AgentOutput, ReplyType
from atguigu.app.schemas.run import AgentRunRequest
from atguigu.agent.harness.run.context import ContextCompiler
from atguigu.agent.harness.validator.output import AgentOutputValidator, ValidatedAgentOutput


class AgentExecutor:
    """Agent 执行器：负责上下文编译、模型调用、输出校验及自我纠错重试。"""

    # 最大执行尝试次数（包含首次调用）
    MAX_CORRECTION_ATTEMPTS: Final[int] = 2

    def __init__(self, agent: Any, output_validator: AgentOutputValidator):
        self.agent = agent
        self.context_compiler = ContextCompiler()
        self.output_validator = output_validator

    async def execute(self,
                      request: AgentRunRequest,
                      runtime_context: AgentRuntimeContext) -> ValidatedAgentOutput:
        """
        职责：执行 Agent 调用，并对可纠正的输出错误有限重试。
        1. 上下文构建器 构建上下文（消息+..）
        2. 调用Agent，Agent的输出
        3. 校验器 校验Agent输出(可信的结果)
        """
        # 1. 编译上下文并创建本次 Run 共用的 Token 统计器
        messages = self.context_compiler.compile_messages(request)
        usage_callback = UsageMetadataCallbackHandler()

        # 2. 执行带有明确次数上限的 Agent 生成和纠错
        validated_output = await self._execute_with_correction(
            messages,
            runtime_context,
            usage_callback
        )

        # 3. 将全部模型调用和纠错消耗合并到可信输出
        return validated_output.model_copy(
            update={
                "token_usage": self._summarize_token_usage(
                    usage_callback
                )
            }
        )

    async def _execute_with_correction(
            self,
            messages: list[Any],
            runtime_context: AgentRuntimeContext,
            usage_callback: UsageMetadataCallbackHandler
    ) -> ValidatedAgentOutput:
        """在允许的有限次数内执行 Agent 生成和自动纠错。"""
        current_messages = messages
        attempt = 0

        while True:
            try:
                # 1. 调用底层 Agent
                raw_agent_output = await self._invoke_agent(
                    current_messages,
                    runtime_context,
                    usage_callback
                )

                # 2. 解析并规范化模型输出
                normalized_agent_output = self._normalize_agent_output(raw_agent_output)

                # 3. 执行业务层面和服务端规则校验
                return await self._validate_agent_output(
                    normalized_agent_output,
                    runtime_context.run_id
                )
            except ToolCallLimitExceededError:
                # 4. 工具超限时使用固定拒绝结果完成当前 Run
                return self._build_tool_limit_output()

            except AgentOutputValidationError as exc:
                # 5. 无法继续纠错时转换成稳定执行错误
                is_last_attempt = (
                        attempt == self.MAX_CORRECTION_ATTEMPTS - 1
                )
                if (
                        is_last_attempt
                        or not OutputCorrectionRules.can_correct(exc)
                ):
                    raise AgentExecutionError(
                        exc.code,
                        str(exc)
                    ) from exc

                # 6. 保留本轮轨迹并追加下一轮纠错反馈
                current_messages = self._build_correction_messages(
                    raw_agent_output,
                    exc
                )
                attempt += 1

    async def _invoke_agent(
            self,
            messages: list[Any],
            runtime_context: AgentRuntimeContext,
            usage_callback: UsageMetadataCallbackHandler
    ) -> Any:
        """调用共享 Agent，并处理调用异常和工具超限"""
        try:
            # 1. 使用当前模型消息和运行上下文调用 Agent
            return await self.agent.ainvoke(
                {"messages": messages},
                context=runtime_context,
                config={"callbacks": [usage_callback]}
            )
        except ToolCallLimitExceededError:
            # 2. 将工具超限交给执行主流程生成安全结果
            raise
        except Exception as exc:
            # 3. 将模型服务和 Agent 调用异常转换成执行错误
            raise AgentExecutionError(
                TerminalErrorCode.MODEL_CALL_FAILED,
                "模型调用失败"
            ) from exc

    @staticmethod
    def _normalize_agent_output(raw_output: Any) -> AgentOutput:
        """提取并校验 Agent 返回的结构化结果"""
        try:
            # 1. 使用模型适配器提取 AgentOutput
            return ModelAdapter.normalize_output(raw_output)
        except ValidationError as exc:
            # 2. 将结构不完整结果转换成可纠正的输出错误
            raise AgentOutputValidationError(
                CorrectableErrorCode.MODEL_OUTPUT_INVALID,
                "模型返回的结构化结果不符合约定"
            ) from exc

    async def _validate_agent_output(
            self,
            output: AgentOutput,
            run_id: str
    ) -> ValidatedAgentOutput:
        """执行回答事实和页面动作的服务端校验"""
        try:
            # 1. 使用当前 Run 的工具证据校验 Agent 输出
            return await self.output_validator.validate(output, run_id)

        except AgentOutputValidationError:
            # 2. 保留可识别的业务校验错误供执行器纠错
            raise
        except Exception as exc:
            # 3. 将校验器内部未知异常转换成统一执行错误
            raise AgentExecutionError(
                TerminalErrorCode.OUTPUT_VALIDATION_FAILED,
                "Agent 输出校验失败"
            ) from exc

    @staticmethod
    def _build_tool_limit_output() -> ValidatedAgentOutput:
        """构建工具调用次数超限后的固定拒绝结果"""
        # 1. 返回不包含业务事实和页面动作的可信安全回复
        return ValidatedAgentOutput(
            reply_type=ReplyType.DECLINE,
            reply_content=(
                "本次查询调用业务工具次数过多，"
                "暂时无法完成查询。"
            )
        )

    @staticmethod
    def _build_correction_messages(
            raw_output: Any,
            error: AgentOutputValidationError
    ) -> list[Any]:
        """保留本轮轨迹，并追加纠错反馈提示。"""
        return [
            *raw_output["messages"],
            OutputCorrectionRules.build_feedback(error)
        ]

    @staticmethod
    def _summarize_token_usage(
            usage_callback: UsageMetadataCallbackHandler
    ) -> dict[str, int]:
        """汇总本次 Run 中全部模型调用的 Token 用量。"""
        usage_items = list(
            usage_callback.usage_metadata.values()
        )
        return {
            "input_tokens": sum(
                item.get("input_tokens", 0)
                for item in usage_items
            ),
            "output_tokens": sum(
                item.get("output_tokens", 0)
                for item in usage_items
            ),
        }
