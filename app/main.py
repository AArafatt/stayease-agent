"""FastAPI application for the StayEase booking agent."""

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage

from agent.graph import agent
from agent.state import AgentState
from app.schemas import (
    ChatMessage,
    ConversationHistoryResponse,
    ErrorResponse,
    MessageRequest,
    MessageResponse,
)
from db.database import async_session
from db.models import Conversation

app = FastAPI(
    title="StayEase AI Agent",
    description="AI-powered booking assistant for short-term accommodation rentals in Bangladesh",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/api/chat/{conversation_id}/message",
    response_model=MessageResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Send a guest message",
)
async def send_message(conversation_id: str, body: MessageRequest) -> MessageResponse:
    """Process a guest message through the LangGraph agent and return the reply."""

    # Upsert conversation record
    async with async_session() as session:
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None:
            conversation = Conversation(
                id=conversation_id,
                guest_name=body.guest_name,
                messages=[],
                context={},
            )
            session.add(conversation)

        # Build initial state from persisted context + new message
        prior_messages: list = []
        for msg in conversation.messages or []:
            cls = HumanMessage if msg["role"] == "human" else AIMessage
            prior_messages.append(cls(content=msg["content"]))

        prior_messages.append(HumanMessage(content=body.message))

        initial_state: AgentState = {
            "messages": prior_messages,
            "intent": "unknown",
            "location": (conversation.context or {}).get("location"),
            "check_in": (conversation.context or {}).get("check_in"),
            "check_out": (conversation.context or {}).get("check_out"),
            "num_guests": (conversation.context or {}).get("num_guests"),
            "listing_id": (conversation.context or {}).get("listing_id"),
            "guest_name": body.guest_name or (conversation.context or {}).get("guest_name"),
            "guest_email": body.guest_email or (conversation.context or {}).get("guest_email"),
            "search_results": None,
            "booking_confirmation": None,
            "conversation_id": conversation_id,
            "error": None,
        }

        # Run the agent graph
        result = await agent.ainvoke(initial_state)

        # Extract reply
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        reply_text = ai_messages[-1].content if ai_messages else "I'm sorry, something went wrong."

        # Persist updated messages & context
        now = datetime.now(timezone.utc).isoformat()
        conversation.messages = (conversation.messages or []) + [
            {"role": "human", "content": body.message, "timestamp": now},
            {"role": "ai", "content": reply_text, "timestamp": now},
        ]
        conversation.intent = result.get("intent")
        conversation.context = {
            "location": result.get("location"),
            "check_in": result.get("check_in"),
            "check_out": result.get("check_out"),
            "num_guests": result.get("num_guests"),
            "listing_id": result.get("listing_id"),
            "guest_name": result.get("guest_name"),
            "guest_email": result.get("guest_email"),
        }
        conversation.is_escalated = result.get("intent") == "escalate"

        await session.commit()

    # Build response payload
    data = None
    if result.get("search_results"):
        data = {"properties": result["search_results"]}
    elif result.get("booking_confirmation"):
        data = {"booking": result["booking_confirmation"]}

    return MessageResponse(
        conversation_id=conversation_id,
        reply=reply_text,
        intent=result.get("intent", "unknown"),
        data=data,
    )


@app.get(
    "/api/chat/{conversation_id}/history",
    response_model=ConversationHistoryResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get conversation history",
)
async def get_history(conversation_id: str) -> ConversationHistoryResponse:
    """Retrieve full message history for a conversation."""

    async with async_session() as session:
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        messages = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
            )
            for msg in (conversation.messages or [])
        ]

        return ConversationHistoryResponse(
            conversation_id=conversation.id,
            messages=messages,
            intent=conversation.intent,
            is_escalated=conversation.is_escalated,
        )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "stayease-agent"}
