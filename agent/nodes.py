"""Node functions for the StayEase LangGraph agent.

Each node receives the current AgentState, performs one logical step,
and returns a partial state update.  Nodes are wired together in graph.py.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from agent.state import AgentState
from agent.tools import (
    create_booking,
    get_listing_details,
    search_available_properties,
)

load_dotenv()

# ---------------------------------------------------------------------------
# LLM instance (shared across nodes)
# ---------------------------------------------------------------------------

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

SYSTEM_PROMPT = """You are StayEase Assistant, a helpful AI agent for a short-term \
accommodation rental platform in Bangladesh. You help guests:
1. Search for available properties by location, dates, and number of guests.
2. Get detailed information about a specific property.
3. Create bookings.

If a request falls outside these three capabilities, politely let the guest know \
and offer to connect them with a human agent.

Always be friendly, concise, and use BDT (৳) for prices. When presenting search \
results, format them clearly with property names, prices, and ratings."""


# ---------------------------------------------------------------------------
# 1. Intent classifier
# ---------------------------------------------------------------------------


async def classify_intent(state: AgentState) -> dict[str, Any]:
    """Analyse the latest guest message and classify intent.

    Updates: intent, location, check_in, check_out, num_guests, listing_id
    Next: route_intent (conditional edge)
    """
    messages = state["messages"]

    classification_prompt = [
        SystemMessage(content=(
            "You are an intent classifier. Analyse the user message and return ONLY "
            "a JSON object with these fields:\n"
            '  "intent": one of "search", "details", "book", "escalate"\n'
            '  "location": string or null\n'
            '  "check_in": "YYYY-MM-DD" or null\n'
            '  "check_out": "YYYY-MM-DD" or null\n'
            '  "num_guests": integer or null\n'
            '  "listing_id": integer or null\n'
            '  "guest_name": string or null\n'
            '  "guest_email": string or null\n'
            "Respond with ONLY valid JSON, no markdown or explanation."
        )),
        messages[-1],
    ]

    response = await llm.ainvoke(classification_prompt)

    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        parsed = {"intent": "escalate"}

    return {
        "intent": parsed.get("intent", "unknown"),
        "location": parsed.get("location") or state.get("location"),
        "check_in": parsed.get("check_in") or state.get("check_in"),
        "check_out": parsed.get("check_out") or state.get("check_out"),
        "num_guests": parsed.get("num_guests") or state.get("num_guests"),
        "listing_id": parsed.get("listing_id") or state.get("listing_id"),
        "guest_name": parsed.get("guest_name") or state.get("guest_name"),
        "guest_email": parsed.get("guest_email") or state.get("guest_email"),
    }


# ---------------------------------------------------------------------------
# 2. Action executor — runs the appropriate tool
# ---------------------------------------------------------------------------


async def execute_action(state: AgentState) -> dict[str, Any]:
    """Invoke the correct tool based on the classified intent.

    Updates: search_results | booking_confirmation | error
    Next: respond
    """
    intent = state["intent"]

    if intent == "search":
        if not all([state.get("location"), state.get("check_in"), state.get("check_out"), state.get("num_guests")]):
            return {"error": "I need your destination, travel dates, and number of guests to search."}

        results = await search_available_properties.ainvoke({
            "location": state["location"],
            "check_in": state["check_in"],
            "check_out": state["check_out"],
            "num_guests": state["num_guests"],
        })
        return {"search_results": results, "error": None}

    elif intent == "details":
        if not state.get("listing_id"):
            return {"error": "Which property would you like to know more about? Please share the listing number."}

        details = await get_listing_details.ainvoke({
            "listing_id": state["listing_id"],
        })
        return {"search_results": [details], "error": None}

    elif intent == "book":
        if not all([state.get("listing_id"), state.get("guest_name"), state.get("guest_email")]):
            return {"error": "To complete your booking I need the listing number, your name, and email address."}

        confirmation = await create_booking.ainvoke({
            "listing_id": state["listing_id"],
            "guest_name": state["guest_name"],
            "guest_email": state["guest_email"],
            "check_in": state["check_in"],
            "check_out": state["check_out"],
            "num_guests": state["num_guests"],
            "conversation_id": state["conversation_id"],
        })
        return {"booking_confirmation": confirmation, "error": None}

    # intent == "escalate" or unknown
    return {"error": None}


# ---------------------------------------------------------------------------
# 3. Response generator
# ---------------------------------------------------------------------------


async def generate_response(state: AgentState) -> dict[str, Any]:
    """Compose a natural-language reply using tool results and conversation context.

    Updates: messages (appends AI response)
    Next: END
    """
    context_parts: list[str] = []

    if state.get("error"):
        context_parts.append(f"Issue: {state['error']}")

    if state["intent"] == "search" and state.get("search_results"):
        context_parts.append(f"Search results:\n{json.dumps(state['search_results'], indent=2)}")

    if state["intent"] == "details" and state.get("search_results"):
        context_parts.append(f"Listing details:\n{json.dumps(state['search_results'][0], indent=2)}")

    if state["intent"] == "book" and state.get("booking_confirmation"):
        context_parts.append(f"Booking confirmed:\n{json.dumps(state['booking_confirmation'], indent=2)}")

    if state["intent"] == "escalate":
        context_parts.append(
            "The guest's request is outside our capabilities. "
            "Politely explain and offer to connect with a human agent."
        )

    system_context = SYSTEM_PROMPT
    if context_parts:
        system_context += "\n\nContext for your reply:\n" + "\n".join(context_parts)

    response = await llm.ainvoke(
        [SystemMessage(content=system_context)] + state["messages"]
    )

    return {
        "messages": [response],
    }


# ---------------------------------------------------------------------------
# 4. Router (conditional edge function)
# ---------------------------------------------------------------------------


def route_intent(state: AgentState) -> str:
    """Determine the next node based on classified intent.

    Returns: node name — 'execute_action' for actionable intents,
             'generate_response' for escalation / unknown.
    """
    if state["intent"] in ("search", "details", "book"):
        return "execute_action"
    return "generate_response"
