"""Request bodies for the API router, and the caps they enforce.

Conversation history is stateless: the client sends prior turns, so the whole
history is caller-supplied and every turn is validated, not just the latest
(requirements.md §6.4).
"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from api.core.constants import MAX_HISTORY_CHARS, MAX_HISTORY_TURNS, MAX_TURN_CHARS


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_TURN_CHARS)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("turn content must not be blank")
        return stripped


class ChatRequest(BaseModel):
    message: str = Field(min_length=5, max_length=300)
    history: list[Turn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank")
        return stripped

    @field_validator("history")
    @classmethod
    def history_must_start_with_a_user_turn(cls, turns: list[Turn]) -> list[Turn]:
        """The Messages API requires the first message to be `user`. Rejecting
        here turns a forged history into our 422 rather than Anthropic's 400."""
        if turns and turns[0].role != "user":
            raise ValueError("history must start with a user turn")
        return turns

    @field_validator("history")
    @classmethod
    def history_must_be_within_total_length(cls, turns: list[Turn]) -> list[Turn]:
        total = sum(len(turn.content) for turn in turns)
        if total > MAX_HISTORY_CHARS:
            raise ValueError(f"history must not exceed {MAX_HISTORY_CHARS} characters")
        return turns
