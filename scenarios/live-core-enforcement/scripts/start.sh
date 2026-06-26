#!/usr/bin/env bash
# Bring up the REAL Agent Assembly stack (aa-gateway + aa-runtime) and run the
# live-core enforcement agent against it.
#
# Run from the scenarios/live-core-enforcement/ directory, or anywhere — the
# script resolves the compose file relative to itself.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENARIO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE="$SCENARIO_DIR/docker-compose.yml"

echo "Starting the real Agent Assembly gateway + runtime..."
docker compose -f "$COMPOSE" up -d aa-gateway aa-runtime

# The runtime image is distroless (no shell), so it carries no in-container
# healthcheck. Gate readiness from the host instead: the runtime publishes its
# health endpoint on :8080 and the gateway its gRPC port on :50051.
echo "Waiting for the runtime health endpoint and gateway gRPC port..."
MAX_WAIT=120
ELAPSED=0

runtime_ready() {
  curl -fsS -o /dev/null "http://localhost:8080/ready" 2>/dev/null
}

gateway_ready() {
  # No shell/grpcurl in the images — a plain TCP connect to :50051 from the host
  # is enough to know the gateway is accepting connections.
  (exec 3<>/dev/tcp/localhost/50051) 2>/dev/null && exec 3>&- 3<&-
}

until { runtime_ready && gateway_ready; } || [[ $ELAPSED -ge $MAX_WAIT ]]; do
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

if [[ $ELAPSED -ge $MAX_WAIT ]]; then
  echo "ERROR: the gateway/runtime did not become ready within ${MAX_WAIT}s." >&2
  echo "Logs: docker compose -f $COMPOSE logs aa-gateway aa-runtime" >&2
  exit 1
fi

echo ""
echo "Gateway + runtime are ready. Running the live agent..."
echo ""

# Run the agent and stream its output. It exits non-zero if no deny was observed.
docker compose -f "$COMPOSE" up --build --exit-code-from live-agent live-agent

echo ""
echo "Stop the stack when done:"
echo "  bash scripts/stop.sh"
