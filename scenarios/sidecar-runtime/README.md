# Sidecar Runtime Scenario

Demonstrates how to run AI agent examples against a **local Agent Assembly
runtime** using Docker Compose — the same pattern used in development and
staging environments before connecting to a production gateway.

## Concept

In production, every agent process runs alongside an Agent Assembly sidecar that
intercepts tool calls and enforces policy. The agent reaches it **through the
SDK** — it never speaks the gateway's wire protocol itself. The SDK's
`init_assembly` / `initAssembly` entrypoint opens a session, and the SDK's
client transport (aa-sdk-client) talks to core over gRPC/UDS:

```
┌──────────────────────────────────────────────────────────┐
│  Your machine                                              │
│                                                            │
│  ┌──────────────────┐                                      │
│  │  python-agent /  │   init_assembly() / client.call_tool │
│  │  node-agent      │                                       │
│  └────────┬─────────┘                                      │
│           │  Agent Assembly SDK                            │
│           ▼                                                 │
│  ┌──────────────────┐   aa-sdk-client (gRPC/UDS)           │
│  │  SDK client      │ ─────────────────────────────►       │
│  └──────────────────┘ ◄─────────────────────────────       │
│                          policy decision + audit record     │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Docker Compose                                        │ │
│  │  assembly-gateway (core)                               │ │
│  │    :8080  (SDK session + governed calls)               │ │
│  │    :50051 (gRPC, production transport)                 │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

The `assembly-gateway` container in this example is a **lightweight mock** that
stands in for core. The agents do **not** call its endpoints directly — they go
through the SDK, and the SDK's client connects to it. Swap the image for the
real gateway image when you have access to it.

> **Architecture note (ADR 0004):** agents always govern tool calls through the
> SDK entrypoint, never by hand-rolling HTTP requests to core. The SDK owns all
> transport to core via aa-sdk-client. This example mirrors that: the only thing
> talking to the gateway is the SDK client.

## Prerequisites

- **Docker** 24+ with Compose v2 (`docker compose`)
- **Python** 3.9+ (for the Python agent example)
- **Node.js** 18+ (for the Node.js agent example)

The agent examples also run **offline** (without Docker) by omitting
`ASSEMBLY_GATEWAY_URL`. The SDK then uses an offline fallback policy.

## Ports and environment variables

| Service           | Port  | Protocol | Environment variable     |
|-------------------|-------|----------|--------------------------|
| assembly-gateway  | 8080  | HTTP     | `ASSEMBLY_GATEWAY_URL`   |
| assembly-gateway  | 50051 | gRPC     | _(production only)_      |

Set `ASSEMBLY_GATEWAY_URL=http://localhost:8080` before running agents when the
gateway container is up. This is the **core address the SDK connects to** — the
agent code itself never reads it beyond passing it to `init_assembly`.

## Setup and run

### 1 — Start the local runtime

```bash
cd scenarios/sidecar-runtime
bash scripts/start.sh
```

This runs `docker compose up -d` and waits until the gateway health check passes.

### 2 — Run the Python agent

```bash
export ASSEMBLY_GATEWAY_URL=http://localhost:8080
python examples/python-agent/agent.py
```

### 3 — Run the Node.js agent

```bash
export ASSEMBLY_GATEWAY_URL=http://localhost:8080
node examples/node-agent/agent.js
```

### 4 — Stop and clean up

```bash
bash scripts/stop.sh
```

## How the agents use the SDK

Both agents demonstrate governance through the SDK. A real integration uses the
published SDK surface (the two SDKs differ — Python governs via the runtime
interceptor the framework examples wire up; Node wraps tools with `withAssembly`):

```python
# Python — real integration. init_assembly() registers the agent and wires the
# detected framework adapter; the runtime interceptor governs each tool call via
# check_tool_start (see the python/ framework examples). To dispatch a governed
# call through the client directly, dispatch_tool takes a tool name and an args
# dict and is async — there is no client.call_tool:
import asyncio
from agent_assembly import init_assembly

async def main():
    with init_assembly(gateway_url=GATEWAY_URL, agent_id="my-agent") as ctx:
        await ctx.client.dispatch_tool("read_file", {"path": "/data/report.csv"})

asyncio.run(main())
```

```js
// Node — real integration. withAssembly() wraps each tool's execute() with a
// pre-execution governance check; a deny throws PolicyViolationError before the
// tool body runs. There is no ctx.client.callTool:
import { withAssembly, PolicyViolationError } from "@agent-assembly/sdk";

const tools = withAssembly(
  { read_file: { execute: async ({ path }) => readReport(path) } },
  { gatewayClient, agentId: "my-agent" },
);
await tools.read_file.execute({ path: "/data/report.csv" });
```

To keep this scenario install-free and runnable offline, each agent ships a tiny
local stand-in for the SDK (clearly marked in the source). The stand-in uses a
simplified `init_assembly` → `client.call_tool` shape purely for readability; the
published SDK governs calls through the interceptor / `withAssembly` wrapper shown
above, not a `call_tool` method. Either way, governed calls route through the SDK
client to core — never via ad-hoc HTTP from the agent.

## Expected output

When the gateway is running:

```
=== Agent Assembly — Sidecar Runtime Example ===

Core:    http://localhost:8080  (connected via SDK)

--- Calling governed tools via the SDK -> local runtime ---

  → read_file(path='/data/report.csv')
  [GATEWAY] decision=allow   reason=permitted by default policy
    ✓ allowed

  Audit ID: audit-...
  → delete_file(path='/data/important.csv')
  [GATEWAY] decision=deny    reason=destructive operations are blocked by policy
    ✗ denied

  Audit ID: audit-...
Total tool calls: 2
```

When running offline (no gateway):

```
=== Agent Assembly — Sidecar Runtime Example ===

Core:    not configured — SDK running in offline mode
         Set ASSEMBLY_GATEWAY_URL=http://localhost:8080 to connect.
         See scripts/start.sh to start the local runtime.

--- Calling governed tools via the SDK (offline policy) ---

  ...same allow/deny output using the SDK's offline fallback policy...
```

## Troubleshooting

**`docker compose` not found?**  
Ensure Docker Desktop ≥ 4.x or Docker Engine with Compose v2 is installed.
`docker compose version` should return `v2.x.x`.

**Gateway health check fails / containers not starting?**  
Run `docker compose logs assembly-gateway` in the `sidecar-runtime/` directory
to inspect container output.

**Port 8080 already in use?**  
Change the host port in `docker-compose.yml`:
```yaml
ports:
  - "18080:8080"   # use host port 18080 instead
```
Then set `ASSEMBLY_GATEWAY_URL=http://localhost:18080`.

**Agent prints "offline mode" even though Docker is running?**  
Check that `ASSEMBLY_GATEWAY_URL` is exported in your shell:
```bash
export ASSEMBLY_GATEWAY_URL=http://localhost:8080
```

## Notes on production usage

- In production, replace the `mock-gateway` build in `docker-compose.yml` with
  the real Agent Assembly gateway image from your container registry.
- The real gateway uses gRPC (port 50051) as the primary transport; the SDK's
  aa-sdk-client connects over it. The HTTP port backs the REST API and dashboard.
- Agent identity, API keys, and policy are configured in the gateway — not in
  the agent script itself.
- The `ASSEMBLY_GATEWAY_URL` environment variable is the only change needed to
  point the SDK at a different environment (local → staging → production).
