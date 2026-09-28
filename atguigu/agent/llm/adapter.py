"""
封装不同的模型
ds

openai
"""
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek

from atguigu.agent.llm.output import AgentOutput
from atguigu.common.config import get_settings


class ModelAdapter:

    @classmethod
    def create_model(cls):

        """
        职责：创建deepseek和qw大语言模型实例
        """
        settings = get_settings()

        # 1. 模型参数
        model_kwargs: dict[str, Any] = {

            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
            "api_key": settings.llm_api_key,
            "temperature": 0,
            "timeout": settings.llm_timeout_seconds
        }

        # 2. 兼容不同的模型提供商的思考模型(关闭思考模式)
        if settings.llm_provider == "deepseek":
            return ChatDeepSeek(
                **model_kwargs,
                extra_body={
                    "thinking": {
                        "type": settings.llm_thinking_mode
                    }
                }
            )

        if settings.llm_provider == "qwen":
            return ChatOpenAI(
                **model_kwargs,
                use_responses_api=False,  # responses_api:响应模式
                extra_body={
                    "enable_thinking": settings.llm_thinking_mode == "enabled"
                }
            )

        return ChatOpenAI(**model_kwargs, use_responses_api=False)

    @staticmethod
    def normalize_output(value: Any) -> AgentOutput:
        """从 Agent 执行结果中提取并校验结构化输出。"""
        structured_output = (
            value.get("structured_response")
            if isinstance(value, dict)
            else value
        )
        if isinstance(structured_output, AgentOutput):
            return structured_output
        return AgentOutput.model_validate(structured_output)
