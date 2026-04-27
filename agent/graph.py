"""LangGraph graph construction for the StayEase booking agent.

This module wires together the nodes defined in nodes.py into an
executable state-machine graph with conditional routing.
"""

from langgraph.graph import END, StateGraph

from agent.nodes import (
    classify_intent,
    execute_action,
    generate_response,
    route_intent,
)
from agent.state import AgentState

# ---------------------------------------------------------------------------
# Graph definition
# ---------------------------------------------------------------------------


def build_agent_graph() -> StateGraph:
    """Construct and compile the StayEase agent graph.

    Flow:
        START
          │
          ▼
      classify_intent
          │
          ├─ search / details / book ──▶ execute_action ──▶ generate_response ──▶ END
          │
          └─ escalate / unknown ──────────────────────────▶ generate_response ──▶ END

    Returns:
        A compiled LangGraph StateGraph ready to be invoked.
    """
    graph = StateGraph(AgentState)

    # --- Register nodes ---
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("execute_action", execute_action)
    graph.add_node("generate_response", generate_response)

    # --- Define edges ---
    graph.set_entry_point("classify_intent")

    # Conditional edge: route based on intent
    graph.add_conditional_edges(
        source="classify_intent",
        path=route_intent,
        path_map={
            "execute_action": "execute_action",
            "generate_response": "generate_response",
        },
    )

    # After executing an action, always generate a response
    graph.add_edge("execute_action", "generate_response")

    # After generating a response, end the turn
    graph.add_edge("generate_response", END)

    return graph.compile()


# Pre-built agent instance for import convenience
agent = build_agent_graph()
