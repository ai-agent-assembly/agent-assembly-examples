"""Governance wiring for the google-adk-governed-agent example.

The ``GoogleADKAdapter.register_hooks`` patches ``google.adk.tools.BaseTool``,
but ADK 1.x concrete tools (``FunctionTool`` and custom ``BaseTool``
subclasses) override ``run_async``, so the base-class patch does not intercept
them. To exercise the *real* governance code path offline, this module applies
the adapter's tool patch to the concrete demo tool class directly — the same
mechanism the Agent Assembly SDK's own integration tests use.

This keeps the demo fully offline (no Gemini / Vertex AI credentials, no
network) while still running the genuine allow / deny / pending governance
logic from the Google ADK adapter.
"""
from __future__ import annotations

from typing import Any

from agent_assembly.adapters.google_adk import patch as google_adk_patch


def govern_tool_class(tool_cls: type[Any], interceptor: Any) -> None:
    """Attach Agent Assembly governance to a concrete ADK tool class.

    Wraps the class's ``run_async`` so every invocation is checked against the
    interceptor (``check_tool_start`` / ``wait_for_tool_approval``) before the
    tool body runs.
    """
    google_adk_patch._apply_tool_run_async_patch(tool_cls, interceptor)


def ungovern_tool_class(tool_cls: type[Any]) -> None:
    """Revert governance hooks installed by ``govern_tool_class``."""
    google_adk_patch._revert_tool_run_async_patch(tool_cls)
