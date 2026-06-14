"""LangGraph state graph for the langgraph-governed-agent example.

Builds a small linear graph whose nodes call governed tools:

    START → research → report → END

Each node calls a tool through the LangChain ``AssemblyCallbackHandler``.
Agent Assembly's ``LangGraphAdapter`` wraps the compiled graph's nodes, so
governance is enforced when the graph is invoked — no live LLM is required.
"""
from __future__ import annotations

from typing import TypedDict
from uuid import uuid4

from agent_assembly.adapters.langchain import AssemblyCallbackHandler


class GraphState(TypedDict):
    """Shared state threaded through the graph nodes."""

    topic: str
    notes: str
    output: str


def _research_node(handler: AssemblyCallbackHandler, state: GraphState) -> GraphState:
    """Safe node: calls the allowed ``get_weather`` tool."""
    handler.on_tool_start(
        serialized={"name": "get_weather"},
        input_str=f'{{"topic": "{state["topic"]}"}}',
        run_id=uuid4(),
    )
    return {**state, "notes": f"Gathered notes about {state['topic']} (mock)."}


def _report_node(handler: AssemblyCallbackHandler, state: GraphState) -> GraphState:
    """Destructive node: calls the denied ``delete_files`` tool."""
    handler.on_tool_start(
        serialized={"name": "delete_files"},
        input_str='{"path": "/etc/passwd"}',
        run_id=uuid4(),
    )
    return {**state, "output": "deleted (should not be reached)"}


def build_graph(handler: AssemblyCallbackHandler) -> object:
    """Compile a governed two-node LangGraph state graph.

    Importing ``langgraph`` lazily keeps the policy module import-safe even
    when the framework is not installed.
    """
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(GraphState)
    graph.add_node("research", lambda state: _research_node(handler, state))
    graph.add_node("report", lambda state: _report_node(handler, state))
    graph.add_edge(START, "research")
    graph.add_edge("research", "report")
    graph.add_edge("report", END)
    return graph.compile()
