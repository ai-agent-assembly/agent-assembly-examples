#!/usr/bin/env node
/**
 * Sidecar-runtime scenario — Agent Assembly examples
 *
 * Demonstrates running an AI agent against a local Agent Assembly runtime
 * sidecar *through the SDK*, the way a real integration does:
 *
 *     your agent
 *         │  initAssembly(...) / client.callTool(...)
 *         ▼
 *     Agent Assembly SDK (@agent-assembly/sdk)
 *         │  aa-sdk-client (gRPC / UDS)
 *         ▼
 *     Agent Assembly core (the gateway / runtime sidecar)
 *
 * The agent never speaks the gateway's wire protocol itself. It calls the SDK's
 * `initAssembly` entrypoint, and the SDK's client transport (aa-sdk-client)
 * talks to core. This mirrors ADR 0004: examples demonstrate the SDK path,
 * never hand-rolled HTTP calls to core endpoints.
 *
 * In a real project you would write:
 *
 *     import { initAssembly } from '@agent-assembly/sdk';
 *     const ctx = await initAssembly({ gatewayUrl, agentId: 'my-agent' });
 *     await ctx.client.callTool('read_file', { path: '/data/report.csv' });
 *
 * This standalone example ships a tiny local stand-in for that SDK surface so
 * it runs with no extra install (and offline, with no Docker), while keeping
 * the same init -> callTool -> audit-event shape as the real SDK.
 *
 * Usage (with the local runtime / mock core):
 *   bash scripts/start.sh
 *   export ASSEMBLY_GATEWAY_URL=http://localhost:8080
 *   node examples/node-agent/agent.js
 *
 * Usage (offline, no Docker needed):
 *   node examples/node-agent/agent.js
 */

'use strict';

const http = require('node:http');

// ---------------------------------------------------------------------------
// Minimal stand-in for the Agent Assembly SDK.
//
// In a real integration you would `import { initAssembly } from
// '@agent-assembly/sdk'` instead of defining these helpers. The SDK's client
// owns *all* transport to core (aa-sdk-client over gRPC/UDS); the agent only
// ever calls `initAssembly` and `client.callTool`. This shim keeps that exact
// surface so the example is faithful to the SDK path while remaining
// install-free and runnable offline.
// ---------------------------------------------------------------------------

// Offline fallback policy, applied by the SDK shim when no core is reachable.
// The real SDK obtains decisions from core; this only exists so the example
// runs without Docker.
const OFFLINE_POLICY = {
  delete_file:   { decision: 'deny',  reason: 'destructive operations are blocked by policy' },
  drop_database: { decision: 'deny',  reason: 'destructive operations are blocked by policy' },
};

function postJson(url, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const u = new URL(url);
    const req = http.request(
      {
        hostname: u.hostname,
        port: u.port || 80,
        path: u.pathname,
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) },
      },
      res => {
        let chunks = '';
        res.on('data', chunk => { chunks += chunk; });
        res.on('end', () => {
          try { resolve(JSON.parse(chunks)); } catch { reject(new Error('Invalid JSON response')); }
        });
      },
    );
    req.setTimeout(5000, () => { req.destroy(); reject(new Error('Request timed out')); });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

/**
 * Stand-in for the SDK client returned by `initAssembly`.
 *
 * Owns the connection to core. When a gateway URL is configured it performs
 * the SDK connect handshake and forwards governed calls to core; otherwise it
 * evaluates the offline fallback policy locally. The agent code below never
 * touches transport details — it only calls `callTool`.
 */
class AssemblyClient {
  constructor({ gatewayUrl, agentId }) {
    this.gatewayUrl = (gatewayUrl || '').replace(/\/$/, '');
    this.agentId = agentId;
    this.connected = false;
    this.networkMode = 'offline';
  }

  async connect() {
    if (!this.gatewayUrl) return;
    try {
      await postJson(`${this.gatewayUrl}/v1/connect`, { agent_id: this.agentId });
      this.connected = true;
      this.networkMode = 'connected';
    } catch (err) {
      console.log(`  [WARN] Core unreachable (${err.message}); using offline fallback policy.`);
    }
  }

  async close() {
    this.connected = false;
  }

  async callTool(tool, inputs) {
    if (this.connected) {
      try {
        return await postJson(`${this.gatewayUrl}/v1/agent/tool-call`, {
          agent_id: this.agentId,
          tool,
          inputs,
        });
      } catch (err) {
        console.log(`  [WARN] Core call failed (${err.message}); using offline fallback policy.`);
      }
    }
    return OFFLINE_POLICY[tool] ?? { decision: 'allow', reason: 'permitted by default policy' };
  }
}

/**
 * Stand-in for `agent_assembly`'s `initAssembly`. Builds the SDK client and
 * opens the session to core. The agent uses the returned context's `client`
 * to make governed calls.
 */
async function initAssembly({ gatewayUrl, agentId }) {
  const client = new AssemblyClient({ gatewayUrl, agentId });
  await client.connect();
  return { client };
}

// ---------------------------------------------------------------------------
// Example agent
// ---------------------------------------------------------------------------

const GATEWAY_URL = (process.env.ASSEMBLY_GATEWAY_URL || '').replace(/\/$/, '');

async function run() {
  console.log('=== Agent Assembly — Sidecar Runtime Example ===\n');

  const { client } = await initAssembly({ gatewayUrl: GATEWAY_URL, agentId: 'sidecar-demo-agent' });

  try {
    if (client.connected) {
      console.log(`Core:    ${client.gatewayUrl}  (connected via SDK)\n`);
    } else {
      console.log('Core:    not configured — SDK running in offline mode');
      console.log('         Set ASSEMBLY_GATEWAY_URL=http://localhost:8080 to connect.');
      console.log('         See scripts/start.sh to start the local runtime.\n');
    }

    const calls = [
      { tool: 'read_file',   inputs: { path: '/data/report.csv' } },
      { tool: 'delete_file', inputs: { path: '/data/important.csv' } },
    ];

    const mode = client.connected ? 'via the SDK -> local runtime' : 'via the SDK (offline policy)';
    console.log(`--- Calling governed tools ${mode} ---\n`);

    for (const { tool, inputs } of calls) {
      const argsStr = Object.entries(inputs)
        .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
        .join(', ');
      console.log(`  → ${tool}(${argsStr})`);

      const response = await client.callTool(tool, inputs);
      const { decision = 'unknown', reason = '', audit_id: auditId } = response;

      if (decision === 'allow') {
        console.log(`  [GATEWAY] decision=allow   reason=${reason}`);
        console.log(`    ✓ allowed\n`);
      } else {
        console.log(`  [GATEWAY] decision=deny    reason=${reason}`);
        console.log(`    ✗ denied\n`);
      }

      if (auditId) {
        console.log(`  Audit ID: ${auditId}`);
      }
    }

    console.log(`Total tool calls: ${calls.length}`);
  } finally {
    await client.close();
  }
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
