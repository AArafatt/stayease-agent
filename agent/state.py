"""LangGraph state definition for the StayEase booking agent."""

from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Conversation state passed between all nodes in the agent graph.

    Each field captures a specific piece of context that nodes read/write
    as the conversation progresses from intent detection to action execution.
    """

    messages: list[BaseMessage]
    """Full message history — drives LLM context and is returned to the guest."""

    intent: Literal["search", "details", "book", "escalate", "unknown"]
    """Classified guest intent — determines which action node runs next."""

    location: str | None
    """Target city or area extracted from the guest's query (e.g. "Cox's Bazar")."""

    check_in: str | None
    """Desired check-in date in ISO format (YYYY-MM-DD)."""

    check_out: str | None
    """Desired check-out date in ISO format (YYYY-MM-DD)."""

    num_guests: int | None
    """Number of guests the property must accommodate."""

    listing_id: int | None
    """Specific listing the guest is asking about or wants to book."""

    guest_name: str | None
    """Guest's name — required to finalise a booking."""

    guest_email: str | None
    """Guest's email — required to finalise a booking."""

    search_results: list[dict] | None
    """Properties returned by the most recent search."""

    booking_confirmation: dict | None
    """Confirmation payload after a booking is successfully created."""

    conversation_id: str
    """Unique conversation identifier — ties messages to the DB record."""

    error: str | None
    """Populated when a tool or node encounters a recoverable error."""
