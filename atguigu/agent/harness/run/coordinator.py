import time
import logging
from time import perf_counter

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.agent.harness.errors import AgentExecutionError, TerminalErrorCode
from atguigu.agent.harness.run.runtime import AgentRuntimeContext
from atguigu.app.repositories.run import AgentRunRepository
from atguigu.app.schemas.run import AgentRunRequest
from atguigu.common.config import get_settings
from atguigu.common.utils import get_utcnow
from atguigu.agent.harness.run.events import build_response_event
from atguigu.agent.harness.run.executor import AgentExecutor
from atguigu.agent.harness.run.output import AgentRunOutPutMapper
from atguigu.models.models import AgentRun, AgentRunState

logger = logging.getLogger(__name__)


class AgentRunCoordinator:

    def __init__(self, session: AsyncSession, executor: AgentExecutor):
        self.setting = get_settings()
        self.session = session
        self.executor = executor
        self.agent_run_repo = AgentRunRepository(session)

    async def start_run(self,
                        user_id: str,
                        access_token: str,
                        request: AgentRunRequest) -> dict:
        """
        职责：
        1. 创建AgentRun
        2. AgentDecision(决策结构化对象：BaseModel做检验)=调用LLM/执行工具（AgentExecutor）
        3. 根据决策判断逻辑（）
        4. 根据判断逻辑的结果，构建不同事件类型响应数据
        5. 返回出去
        """

        # 1. 创建AgentRun
        agent_run = AgentRun(
            conversation_id=request.conversation_id,
            user_id=user_id,
            turn_id=request.turn_id,
            state=AgentRunState.RUNNING,
            model_name=self.setting.llm_model,
            prompt_version=self.setting.prompt_version,
            input_context=request.model_dump(mode="json"),

        )
        # 2. 保存
        self.agent_run_repo.add_agent_run(agent_run)

        # 3. 提交
        await self.session.commit()

        # 4. 调用执行器执行以及映射AgentRunState对应的数据
        start_time = perf_counter()

        runtime_context = AgentRuntimeContext(
            run_id=agent_run.id,
            conversation_id=agent_run.conversation_id,
            user_id=agent_run.user_id,
            access_token=access_token
        )
        try:
            # a) 调用Agent执行获取可信的结果
            validated_result = await self.executor.execute(request, runtime_context)
            agent_run.input_tokens = validated_result.token_usage[
                "input_tokens"
            ]
            agent_run.output_tokens = validated_result.token_usage[
                "output_tokens"
            ]
            # b) 将可信的结果映射到不同AgentRunState中
            agent_run.state, agent_run.result = AgentRunOutPutMapper.map(validated_result)
        except Exception as exc:
            # c. 区分具有稳定错误码的执行失败和边界之外的未知失败
            if isinstance(exc, AgentExecutionError):
                error_code = exc.code
                logger.exception(
                    "Agent 执行失败 [%s] run_id=%s",
                    error_code,
                    agent_run.id
                )
            else:
                error_code = TerminalErrorCode.AGENT_EXECUTION_FAILED
                logger.exception(
                    "Agent 未知执行异常 run_id=%s",
                    agent_run.id
                )

            # d. 统一保存 Agent 执行失败状态和错误结果
            agent_run.state = AgentRunState.FAILED
            agent_run.error = str(exc)
            agent_run.result = {
                "code": error_code,
                "message": "AI Service 处理失败"
            }

            # 5. 调用响应事件构建器构建返回给customer-service的数据
        agent_run.latency_ms = int((perf_counter() - start_time) * 1000)
        if agent_run.state != AgentRunState.DECISION_PREPARED:
            agent_run.finished_at = get_utcnow()
        await self.session.commit()  # session是同一个，且拥有agent_run，那么直接会修改
        return build_response_event(agent_run)

    async def confirm_run(self,
                          user_id: str,
                          run_id: str) -> dict:
        """
        核心职责：
        1. 从start_run中将决策的结果 获取到
        2. 修改AgentRun的状态（COMPLETED）
        3. 返回结果
        """
        run = await self.agent_run_repo.find_by_id(run_id)
        run.state = AgentRunState.COMPLETED
        run.finished_at = get_utcnow()
        await self.session.commit()
        return build_response_event(run)

    async def cancel_run(self,
                         user_id: str,
                         run_id: str
                         ):
        """
            核心职责：
            修改AgentRun的状态（SUPERSEDED）
        """

        run = await self.agent_run_repo.find_by_id(run_id)
        if run.state == AgentRunState.DECISION_PREPARED:
            run.state = AgentRunState.SUPERSEDED
            run.finished_at = get_utcnow()
            await self.session.commit()


if __name__ == '__main__':
    start = perf_counter()
    time.sleep(2)
    end = perf_counter()
    print(int(end - start) * 1000)
