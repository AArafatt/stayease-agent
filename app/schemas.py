"""Pydantic request / response schemas for the StayEase API."""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class MessageRequest(BaseModel):
    """Body for POST /api/chat/{conversation_id}/message."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["I need a room in Cox's Bazar for 2 nights for 2 guests"],
    )
    guest_name: str | None = Field(default=None, examples=["Rahim Uddin"])
    guest_email: str | None = Field(default=None, examples=["rahim@example.com"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    """Response from the agent after processing a guest message."""

    conversation_id: str
    reply: str
    intent: str
    data: dict | None = Field(
        default=None,
        description="Structured payload — search results, listing details, or booking confirmation",
    )


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str  # "human" | "ai"
    content: str
    timestamp: datetime


class ConversationHistoryResponse(BaseModel):
    """Response for GET /api/chat/{conversation_id}/history."""

    conversation_id: str
    messages: list[ChatMessage]
    intent: str | None = None
    is_escalated: bool = False


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
