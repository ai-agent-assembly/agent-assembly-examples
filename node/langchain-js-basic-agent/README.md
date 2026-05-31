# langchain-js-basic-agent

A LangChain.js-style agent example showing how to integrate the Agent Assembly Node.js SDK for tool governance.

## What this example demonstrates

- Calling `initAssembly()` to connect to an Agent Assembly gateway (or run in offline/noop mode)
- Wrapping tool calls with `withAssembly()` so every execution passes through governance
- One **allowed** tool call (`get_weather`) — executes and logs output
- One **denied** tool call (`delete_file`) — blocked at the policy layer
- Audit events emitted to the gateway on each tool invocation

## Prerequisites

- Node.js >= 20 LTS
- pnpm (`npm install -g pnpm`)

## Install

```bash
pnpm install
```

## Run

```bash
pnpm start
```

### Expected output

```
=== LangChain.js-style Agent Assembly Example ===

Running allowed tool: get_weather
[POLICY ALLOW] get_weather: Weather in Taipei: 22°C, partly cloudy. [mock]

Running denied tool: delete_file
[POLICY DENY] delete_file: Destructive filesystem operations require human approval.

Done. Audit events emitted to gateway (or noop in offline mode).
```

## Test

```bash
pnpm test
```

Tests run in offline mode — no gateway or API keys required.

## TypeScript type check

```bash
pnpm typecheck
```

## Real-provider mode (optional)

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env: set AAASM_GATEWAY_URL and optionally OPENAI_API_KEY
```

Then `pnpm start` will connect to the real gateway and real OpenAI API if configured.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Cannot find module '@agent-assembly/sdk'` | Run `pnpm install` |
| Gateway connection refused | Omit `AAASM_GATEWAY_URL` to use offline mode |
| TypeScript errors | Run `pnpm typecheck` and check Node.js version |

## Links

- [Agent Assembly Node.js SDK](https://github.com/AI-agent-assembly/node-sdk)
- [Node.js examples overview](../README.md)
- [Root examples README](../../README.md)
