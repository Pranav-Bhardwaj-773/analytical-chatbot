from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] | None = Field(default=None, max_length=20)
    last_sql: str | None = Field(default=None, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    sql: str | None = None
    dashboard: dict | None = None