# Sidecar Runtime Scenario

Demonstrates how to run AI agent examples against a **local Agent Assembly
runtime** using Docker Compose — the same pattern used in development and
staging environments before connecting to a production gateway.

## Concept

In production, every agent process runs alongside an Agent Assembly sidecar that
intercepts tool calls and enforces policy. In local development you can spin up
a lightweight gateway container that behaves the same way.

```
┌─────────────────────────────────────────────────┐
│  Your machine                                   │
│                                                 │
│  ┌──────────────────┐     HTTP :8080            │
│  │  python-agent /  │ ─────────────────────►   │
│  │  node-agent      │ ◄─────────────────────   │
│  └──────────────────┘  policy decision +        │
│                         audit record            │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  Docker Compose                          │  │
│  │  assembly-gateway  :8080 (HTTP)          │  │
│  │                    :50051 (gRPC, prod)   │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

The `assembly-gateway` container in this example is a **lightweight mock** that
simulates the gateway API. Swap the image for the real gateway image when you
have access to it.

## Prerequisites

- **Docker** 24+ with Compose v2 (`docker compose`)
- **Python** 3.9+ (for the Python agent example)
- **Node.js** 18+ (for the Node.js agent example)

The agent examples also run **offline** (without Docker) by omitting
`ASSEMBLY_GATEWAY_URL`. An offline fallback policy is used in that case.

## Ports and environment variables

| Service           | Port  | Protocol | Environment variable     |
|-------------------|-------|----------|--------------------------|
| assembly-gateway  | 8080  | HTTP     | `ASSEMBLY_GATEWAY_URL`   |
| assembly-gateway  | 50051 | gRPC     | _(production only)_      |

Set `ASSEMBLY_GATEWAY_URL=http://localhost:8080` before running agents when the
gateway container is up.

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

## Expected output

When the gateway is running:

```
=== Agent Assembly — Sidecar Runtime Example ===

Gateway: http://localhost:8080  (connected)

--- Calling governed tools via the local runtime ---

  → read_file(path='/data/report.csv')
  [GATEWAY] decision=allow   reason=permitted by default policy
    ✓ allowed

  → delete_file(path='/data/important.csv')
  [GATEWAY] decision=deny    reason=destructive operations are blocked by policy
    ✗ denied

Total tool calls: 2
```

When running offline (no gateway):

```
=== Agent Assembly — Sidecar Runtime Example ===

Gateway: not configured — running in offline mode
         Set ASSEMBLY_GATEWAY_URL=http://localhost:8080 to connect.
         See scripts/start.sh to start the local runtime.

--- Calling governed tools via offline policy ---

  ...same output using local mock policy...
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
- The real gateway uses gRPC (port 50051) as the primary transport; the HTTP
  port is for the REST API and dashboard.
- Agent identity, API keys, and policy are configured in the gateway — not in
  the agent script itself.
- The `ASSEMBLY_GATEWAY_URL` environment variable is the only change needed to
  point an agent at a different environment (local → staging → production).
