#!/usr/bin/env python3
"""
Sidecar-runtime scenario — Agent Assembly examples

Demonstrates running an AI agent against a local Agent Assembly runtime sidecar
*through the SDK*, the way a real integration does:

    your agent
        │  init_assembly(...) / ctx.client.dispatch_tool(...)
        ▼
    Agent Assembly SDK
        │  aa-sdk-client (gRPC / UDS)
        ▼
    Agent Assembly core (the gateway / runtime sidecar)

The agent never speaks the gateway's wire protocol itself. It calls the SDK's
``init_assembly`` entrypoint, and the SDK's client transport (aa-sdk-client)
talks to core. This mirrors ADR 0004: examples demonstrate the SDK path, never
hand-rolled HTTP calls to core endpoints.

In a real project you would write:

    from agent_assembly import init_assembly

    with init_assembly(gateway_url=..., agent_id="my-agent") as ctx:
        # dispatch_tool is async and takes the tool name + an args dict.
        await ctx.client.dispatch_tool("read_file", {"path": "/data/report.csv"})

This standalone example ships a tiny local stand-in for that SDK surface so it
runs with no extra install (and offline, with no Docker), while keeping the same
init -> governed-call -> audit-event shape as the real SDK. The stand-in exposes
a synchronous ``call_tool`` for brevity; the real client method is the async
``dispatch_tool`` shown above.

Usage (with the local runtime / mock core):
    bash scripts/start.sh
    export ASSEMBLY_GATEWAY_URL=http://localhost:8080
    python examples/python-agent/agent.py

Usage (offline, no Docker needed):
    python examples/python-agent/agent.py
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Minimal stand-in for the Agent Assembly SDK.
#
# In a real integration you would `from agent_assembly import init_assembly`
# instead of defining these classes. The SDK's client owns *all* transport to
# core (aa-sdk-client over gRPC/UDS); the agent initializes with `init_assembly`
# and issues governed calls via the async `ctx.client.dispatch_tool(name, args)`
# (or lets a framework runtime interceptor wrap its tools automatically). This
# shim keeps that same init -> governed-call shape — with a synchronous
# `call_tool` stand-in for the async `dispatch_tool` — so the example stays
# faithful to the SDK path while remaining install-free and runnable offline.
# ---------------------------------------------------------------------------

# Offline fallback policy, applied by the SDK shim when no core is reachable.
# The real SDK obtains decisions from core; this only exists so the example
# runs without Docker.
_OFFLINE_POLICY: dict[str, tuple[str, str]] = {
    "delete_file": ("deny", "destructive operations are blocked by policy"),
    "drop_database": ("deny", "destructive operations are blocked by policy"),
}


class AssemblyClient:
    """Stand-in for the SDK client returned by ``init_assembly``.

    Owns the connection to core. When a gateway URL is configured it performs
    the SDK connect handshake and forwards governed calls to core; otherwise it
    evaluates the offline fallback policy locally. The agent code below never
    touches transport details — it only calls ``call_tool``.
    """

    def __init__(self, *, gateway_url: str, agent_id: str) -> None:
        self.gateway_url = gateway_url.rstrip("/")
        self.agent_id = agent_id
        self.connected = False
        self.network_mode = "offline"

    # -- SDK lifecycle -------------------------------------------------------

    def connect(self) -> None:
        """Establish the SDK session with core (no-op in offline mode)."""
        if not self.gateway_url:
            return
        try:
            payload = json.dumps({"agent_id": self.agent_id}).encode()
            req = urllib.request.Request(
                f"{self.gateway_url}/v1/connect",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                json.loads(resp.read())
            self.connected = True
            self.network_mode = "connected"
        except OSError as exc:  # URLError subclasses OSError
            print(f"  [WARN] Core unreachable ({exc}); using offline fallback policy.")

    def close(self) -> None:
        self.connected = False

    # -- governed tool call --------------------------------------------------

    def call_tool(self, tool: str, **inputs: Any) -> dict[str, Any]:
        """Submit a governed tool call through the SDK session to core."""
        if self.connected:
            payload = json.dumps(
                {"agent_id": self.agent_id, "tool": tool, "inputs": inputs}
            ).encode()
            req = urllib.request.Request(
                f"{self.gateway_url}/v1/agent/tool-call",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return json.loads(resp.read())
            except OSError as exc:
                print(f"  [WARN] Core call failed ({exc}); using offline fallback policy.")
        decision, reason = _OFFLINE_POLICY.get(
            tool, ("allow", "permitted by default policy")
        )
        return {"decision": decision, "reason": reason, "audit_id": None}


class _AssemblyContext:
    def __init__(self, client: AssemblyClient) -> None:
        self.client = client
        self.network_mode = client.network_mode

    def __enter__(self) -> "_AssemblyContext":
        return self

    def __exit__(self, *exc: object) -> None:
        self.client.close()


def init_assembly(*, gateway_url: str, agent_id: str) -> _AssemblyContext:
    """Stand-in for ``agent_assembly.init_assembly``.

    Builds the SDK client and opens the session to core. The agent uses the
    returned context's ``client`` to make governed calls.
    """
    client = AssemblyClient(gateway_url=gateway_url, agent_id=agent_id)
    client.connect()
    return _AssemblyContext(client)


# ---------------------------------------------------------------------------
# Example agent
# ---------------------------------------------------------------------------

GATEWAY_URL = os.environ.get("ASSEMBLY_GATEWAY_URL", "").rstrip("/")


def run() -> None:
    print("=== Agent Assembly — Sidecar Runtime Example ===\n")

    with init_assembly(gateway_url=GATEWAY_URL, agent_id="sidecar-demo-agent") as ctx:
        client = ctx.client

        if client.connected:
            print(f"Core:    {client.gateway_url}  (connected via SDK)\n")
        else:
            print("Core:    not configured — SDK running in offline mode")
            print("         Set ASSEMBLY_GATEWAY_URL=http://localhost:8080 to connect.")
            print("         See scripts/start.sh to start the local runtime.\n")

        calls: list[tuple[str, dict[str, Any]]] = [
            ("read_file", {"path": "/data/report.csv"}),
            ("delete_file", {"path": "/data/important.csv"}),
        ]

        mode = "via the SDK -> local runtime" if client.connected else "via the SDK (offline policy)"
        print(f"--- Calling governed tools {mode} ---\n")

        for tool, inputs in calls:
            args_str = ", ".join(f"{k}={v!r}" for k, v in inputs.items())
            print(f"  → {tool}({args_str})")
            response = client.call_tool(tool, **inputs)
            decision = response.get("decision", "unknown")
            reason = response.get("reason", "")
            audit_id = response.get("audit_id")

            if decision == "allow":
                print(f"  [GATEWAY] decision=allow   reason={reason}")
                print("    ✓ allowed\n")
            else:
                print(f"  [GATEWAY] decision=deny    reason={reason}")
                print("    ✗ denied\n")

            if audit_id:
                print(f"  Audit ID: {audit_id}")

        print(f"Total tool calls: {len(calls)}")


if __name__ == "__main__":
    run()
