'use strict';

/**
 * Mock Agent Assembly core for local development.
 *
 * Stands in for the real Agent Assembly gateway / runtime sidecar that the SDK
 * (aa-sdk-client) connects to. It is NOT something agents call directly — the
 * agent talks to the SDK, and the SDK's client talks to this endpoint. The
 * surface mirrors the SDK transport, not a public REST API:
 *
 *   GET  /health             — health check
 *   POST /v1/connect         — SDK session handshake (init_assembly / initAssembly)
 *   POST /v1/agent/tool-call  — governed tool call submitted through the SDK session
 *
 * Replace this container with the real gateway image when you have access.
 */

const http = require('node:http');
const { randomUUID } = require('node:crypto');

const LOG_LEVEL = process.env.LOG_LEVEL || 'info';

function log(msg) {
  if (LOG_LEVEL !== 'silent') {
    console.log(`[${new Date().toISOString()}] ${msg}`);
  }
}

// Simple inline policy: deny destructive operations; allow everything else.
const DENY_TOOLS = new Set(['delete_file', 'drop_database', 'truncate_table']);

function evaluate(tool) {
  if (DENY_TOOLS.has(tool)) {
    return { decision: 'deny', reason: 'destructive operations are blocked by policy' };
  }
  return { decision: 'allow', reason: 'permitted by default policy' };
}

function readBody(req) {
  return new Promise(resolve => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); } catch { resolve({}); }
    });
  });
}

function sendJson(res, status, payload) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(payload));
}

const server = http.createServer(async (req, res) => {
  const { method, url } = req;

  // Health check
  if (url === '/health' || url === '/healthz') {
    sendJson(res, 200, { status: 'ok', service: 'assembly-gateway-mock', version: '0.0.1' });
    return;
  }

  // SDK session handshake — the SDK's init_assembly/initAssembly opens a session
  // here before any governed calls. The real core authenticates the agent and
  // returns a session; the mock just acknowledges.
  if (method === 'POST' && url === '/v1/connect') {
    const payload = await readBody(req);
    const agentId = payload.agent_id || 'unknown';
    const sessionId = `sess-${Date.now()}-${randomUUID().slice(0, 8)}`;
    log(`connect agent=${agentId} session=${sessionId}`);
    sendJson(res, 200, { session_id: sessionId, agent_id: agentId });
    return;
  }

  // Governed tool call submitted by the SDK client on behalf of the agent.
  if (method === 'POST' && url === '/v1/agent/tool-call') {
    const payload = await readBody(req);
    const tool = payload.tool || 'unknown';
    const agentId = payload.agent_id || 'unknown';
    const { decision, reason } = evaluate(tool);
    const auditId = `audit-${Date.now()}-${randomUUID().slice(0, 8)}`;

    log(`agent=${agentId} tool=${tool.padEnd(20)} decision=${decision.padEnd(6)} reason=${reason}`);

    sendJson(res, 200, { decision, reason, audit_id: auditId });
    return;
  }

  sendJson(res, 404, { error: 'not found', path: url });
});

const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
  log(`Mock assembly-gateway (core stand-in) listening on :${PORT}`);
  log(`Health check: GET  http://localhost:${PORT}/health`);
  log(`SDK connect:  POST http://localhost:${PORT}/v1/connect`);
  log(`Tool call:    POST http://localhost:${PORT}/v1/agent/tool-call`);
});
