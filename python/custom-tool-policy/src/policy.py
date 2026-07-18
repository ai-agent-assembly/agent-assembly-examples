"""Minimal local policy engine for the custom-tool-policy example.

This example has no framework dependency — only ``agent-assembly``.
The policy engine simulates governance with a simple allow/deny rule set.

``LocalPolicyEngine`` implements the ``check_tool_start`` contract (the public
``GovernanceInterceptor`` protocol in ``agent_assembly.adapters``) in-process so
the demo runs fully offline. It is a stand-in for the gateway, NOT the
production wiring: ``ctx.client`` is a bare ``GatewayClient`` with no
``check_tool_start`` method, so passing it to ``governed()`` makes
``AssemblyCallbackHandler.on_tool_start`` find no check, return without raising,
and allow every tool — governance silently disabled (fail-open). In production
you do not wrap callables against ``ctx.client``; instead run tools through a
supported framework adapter and let ``init_assembly()`` wire the real
gateway-backed interceptor into it. See this example's README "Production mode"
section.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from agent_assembly.adapters.langchain import AssemblyCallbackHandler
from agent_assembly.exceptions import ToolExecutionBlockedError

DENIED_TOOLS: frozenset[str] = frozenset({
    "send_http_request",
    "write_to_disk",
})


class LocalPolicyEngine:
    """Minimal policy engine: deny specific tool names, allow everything else."""

    def check_tool_start(
        self,
        serialized: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, str]:
        tool_name = serialized.get("name", "")
        if tool_name in DENIED_TOOLS:
            return {
                "status": "deny",
                "reason": (
                    f"Tool '{tool_name}' is blocked by policy rule "
                    "'deny_network_and_disk_writes'."
                ),
            }
        return {"status": "allow"}


def governed(tool_name: str, fn: Any, policy: LocalPolicyEngine) -> Any:
    """Wrap a plain Python function with governance.

    Returns a new callable that runs the policy check before calling ``fn``.
    Raises ``ToolExecutionBlockedError`` if the policy denies the tool.
    """
    handler = AssemblyCallbackHandler(interceptor=policy)

    def _wrapper(**kwargs: Any) -> Any:
        import json

        handler.on_tool_start(
            serialized={"name": tool_name, "type": "tool"},
            input_str=json.dumps(kwargs),
            run_id=uuid4(),
        )
        return fn(**kwargs)

    _wrapper.__name__ = tool_name
    return _wrapper
