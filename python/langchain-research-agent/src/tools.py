"""LangChain tools for the langchain-research-agent ReAct example.

Two tools back the research agent:

  - ``web_search``  — a network-egress tool (governed by the allowlist + budget).
  - ``calculator``  — a safe local compute tool (always allowed, zero cost).

In ``--mock`` mode the tools return canned data so the example runs offline
with no API keys and no real network access.
"""
from __future__ import annotations

import ast
import operator

from langchain_core.tools import tool

# Canned search results keyed by a substring of the query, used in --mock mode.
_MOCK_CORPUS: dict[str, str] = {
    "speed of light": "The speed of light in vacuum is 299792458 metres per second.",
    "population of france": "France has a population of approximately 68000000 people.",
    "agent governance": (
        "Agent governance enforces policy on autonomous agents via interception "
        "layers: in-process SDK, sidecar proxy, and kernel eBPF."
    ),
}

# Operators permitted in the safe calculator. eval() is never used.
_SAFE_OPERATORS: dict[type, object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


@tool
def web_search(query: str) -> str:
    """Search the web for information about a topic.

    Returns mock results in offline / demo mode. In production this tool would
    issue an outbound HTTPS request, which Agent Assembly meters against the
    network allowlist and the daily budget.
    """
    lowered = query.lower()
    for key, answer in _MOCK_CORPUS.items():
        if key in lowered:
            return answer
    return f"No high-confidence result found for {query!r} (mock corpus)."


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op = _SAFE_OPERATORS[type(node.op)]
        return op(_eval_node(node.left), _eval_node(node.right))  # type: ignore[operator]
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPERATORS[type(node.op)]
        return op(_eval_node(node.operand))  # type: ignore[operator]
    raise ValueError("unsupported expression")


@tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression, e.g. ``"299792458 / 68000000"``.

    Uses a safe AST evaluator (no ``eval``). Supports + - * / ** % and unary
    minus only.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
    except (ValueError, KeyError, SyntaxError, ZeroDivisionError):
        return f"Could not evaluate {expression!r}."
    return f"{expression} = {result:g}"
