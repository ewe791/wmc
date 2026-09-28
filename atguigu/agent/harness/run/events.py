from typing import Any

from atguigu.models.models import AgentRun, AgentRunState


"""
AgentRunState
作用1：看到Agent运行状态
作用2：作为和customer-service的事件类型（契约）


"""


def _build_event(
    run_id: str,
    event_type: str,
    event_data: dict[str, Any]
) -> dict[str, Any]:
    """构建 Customer Service 能够解析的统一事件结构。"""
    return {
        "event_type": event_type,
        "event_data": {
            "run_id": run_id,
            **event_data
        }
    }


def build_response_event(run: AgentRun) -> dict[str, Any]:
    """根据 AgentRun 当前状态构建对应的响应事件。"""
    if run.state == AgentRunState.COMPLETED:
        return _build_event(
            run.id,
            "run_completed",
            run.result
        )

    if run.state == AgentRunState.HANDED_OFF:
        return _build_event(
            run.id,
            "run_handoff_requested",
            run.result
        )

    if run.state == AgentRunState.DECISION_PREPARED:
        return _build_event(
            run.id,
            "run_decision_prepared",
            {}
        )

    if run.state == AgentRunState.FAILED:
        return _build_event(
            run.id,
            "run_failed",
            run.result
        )

    raise RuntimeError("当前 AgentRun 状态无法构建响应事件")
