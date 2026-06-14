"""Google ADK tool definitions for the google-adk-governed-agent example.

Google ADK runs its agent loop against a cloud LLM (Gemini / Vertex AI), which
requires credentials and a network call — so this example does **not** drive a
live model. Instead it replays a *scripted tool trajectory*: it constructs real
ADK ``BaseTool`` instances and invokes ``run_async`` directly, which is the
exact governance surface the ``GoogleADKAdapter`` patches.

Three tools are defined:
  - get_weather    — safe information tool (ALLOWED by policy)
  - delete_records — destructive tool      (DENIED by policy)
  - send_email     — outbound communication (requires APPROVAL)
"""
from __future__ import annotations

from typing import Any

from google.adk.tools import BaseTool


class DemoTool(BaseTool):
    """A minimal concrete ADK tool with a deterministic, offline result.

    In ADK 1.x every concrete tool overrides ``run_async``; the Agent Assembly
    governance patch is therefore applied to each concrete tool class so the
    policy gate runs before this body executes (see ``governance.py``).
    """

    def __init__(self, name: str, result: str) -> None:
        super().__init__(name=name, description=f"{name} demo tool")
        self._result = result

    async def run_async(self, *, args: dict[str, Any], tool_context: Any) -> str:
        del args, tool_context
        return self._result


def build_tools() -> dict[str, DemoTool]:
    """Build the scripted set of governed demo tools, keyed by name."""
    return {
        "get_weather": DemoTool("get_weather", "Weather: 22C, partly cloudy (mock response)"),
        "delete_records": DemoTool("delete_records", "Deleted records (should not be reached)"),
        "send_email": DemoTool("send_email", "Email sent (should not be reached)"),
    }
