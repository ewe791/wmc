from collections.abc import Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from atguigu.agent.harness.run.runtime import AgentExecutionState, AgentRuntimeContext
from atguigu.agent.harness.skills.catalog import SKILL_CATALOG
from atguigu.agent.llm.output import AgentOutput


class SkillScopeMiddleware(
    AgentMiddleware[
        AgentExecutionState,
        AgentRuntimeContext,
        AgentOutput
    ]
):
    """根据当前 Skill 限制模型可见的工具"""

    async def awrap_model_call(
            self,
            request: ModelRequest[AgentRuntimeContext],
            handler: Callable[
                [ModelRequest[AgentRuntimeContext]],
                Awaitable[ModelResponse[AgentOutput]]
            ]
    ) -> ModelResponse[AgentOutput]:
        """在每次模型调用前应用当前 Skill"""

        # 1. 读取当前 Agent 已经激活的 Skill
        active_skill_code = request.state.get("active_skill_code")

        # 2. 没有 Skill 时提供精简索引并仅保留加载工具
        if active_skill_code is None:
            allowed_tool_names = {"load_skill"}
        else:
            # 3. 已有 Skill 时开放对应工具
            skill = SKILL_CATALOG.get_skill(active_skill_code)
            allowed_tool_names = {
                "load_skill",
                *skill.tools
            }

        # 4. 只向模型提供当前 Skill 允许使用的工具
        scoped_request = request.override(
            tools=[
                tool
                for tool in request.tools
                if tool.name in allowed_tool_names
            ],
            model_settings={
                **request.model_settings,
                "parallel_tool_calls": False
            }
        )
        return await handler(scoped_request)
