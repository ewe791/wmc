from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from atguigu.common.utils import get_uid, get_utcnow


class Base(DeclarativeBase):
    pass


class AgentRunState(StrEnum):
    RUNNING = "RUNNING"
    DECISION_PREPARED = "DECISION_PREPARED"
    COMPLETED = "COMPLETED"
    HANDED_OFF = "HANDED_OFF"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


class AgentRun(Base):
    """记录 AI 对一次 Turn 的处理过程和最终结果。"""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
        default=lambda: get_uid("run")
    )
    conversation_id: Mapped[str] = mapped_column(String(80), index=True)
    user_id: Mapped[str] = mapped_column(String(80), index=True)
    turn_id: Mapped[str] = mapped_column(String(80), index=True)
    state: Mapped[str] = mapped_column(
        String(30),
        default=AgentRunState.RUNNING,
        index=True
    )
    model_name: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(80))
    input_context: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True
    )
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utcnow
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


class AgentToolCall(Base):
    """记录一次 Agent 业务工具调用及其执行结果。"""

    __tablename__ = "agent_tool_calls"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "tool_call_id",
            name="uq_agent_tool_calls_run_call"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
        default=lambda: get_uid("tool")
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("agent_runs.id"),
        index=True
    )
    tool_call_id: Mapped[str] = mapped_column(String(120))
    tool_name: Mapped[str] = mapped_column(String(80), index=True)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True
    )
    success: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utcnow
    )
