from langchain_core.messages import SystemMessage

from atguigu.agent.harness.errors import (
    AgentOutputValidationError,
    CorrectableErrorCode
)


class OutputCorrectionRules:
    """定义服务端输出校验失败后的模型纠错规则。"""

    @staticmethod
    def can_correct(
        error: AgentOutputValidationError
    ) -> bool:
        """判断当前输出错误是否允许交给模型重新生成。"""
        # 1. 仅允许可纠正输出错误码进入模型纠错
        return isinstance(error.code, CorrectableErrorCode)

    @staticmethod
    def build_feedback(
        error: AgentOutputValidationError
    ) -> SystemMessage:
        """将可纠正错误转换成下一次模型调用的反馈消息。"""
        # 1. 将具体校验原因和重新生成边界写入系统反馈
        return SystemMessage(
            content=(
                "上一次最终回复未通过服务端校验："
                f"{error}。请仅根据成功工具结果重新生成回复；"
                "无法确认的业务事实不要回答，未经工具确认的"
                "业务对象不要生成页面动作。"
            )
        )
