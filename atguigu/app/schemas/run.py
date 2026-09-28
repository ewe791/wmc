from typing import Any, Literal

from pydantic import BaseModel, Field


class CurrentMessage(BaseModel):
    message_id: str
    type: Literal["text", "object"]
    content: dict[str, Any]


class HistoryMessage(CurrentMessage):
    role: Literal["user", "ai", "human"]


class AgentRunRequest(BaseModel):
    conversation_id: str
    turn_id: str
    messages: list[CurrentMessage] = Field(min_length=1)
    history: list[HistoryMessage] = Field(default_factory=list)
