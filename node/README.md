# Node.js / TypeScript Examples

Runnable Node.js and TypeScript examples showing how to integrate Agent Assembly with JavaScript AI agent frameworks and vanilla TypeScript code.

## Examples

| Sub-project | Framework | What it demonstrates | Complexity |
|---|---|---|---|
| [`langchain-js-basic-agent/`](./langchain-js-basic-agent/) | LangChain.js | Tool governance hooks in a LangChain.js-style agent | Intermediate |
| [`openai-node-tool-policy/`](./openai-node-tool-policy/) | OpenAI Node SDK | Policy enforcement using OpenAI function-calling format | Intermediate |
| [`custom-tool-policy/`](./custom-tool-policy/) | — (none) | Minimal SDK usage — no agent framework needed | Beginner |

All examples use the `@agent-assembly/sdk` npm package.

## Quick start

Pick any example and run it in three commands:

```bash
cd node/<example-name>
pnpm install
pnpm start
```

To run the smoke tests:

```bash
pnpm test
```

## Prerequisites

- **Node.js** >= 20 LTS — install from [nodejs.org](https://nodejs.org)
- **pnpm** — install via `npm install -g pnpm`
- A running Agent Assembly gateway (optional — all examples default to offline/noop mode)

## Choosing an example

| I want to… | Start with |
|---|---|
| See Agent Assembly with LangChain.js | [`langchain-js-basic-agent/`](./langchain-js-basic-agent/) |
| See Agent Assembly with OpenAI function-calling | [`openai-node-tool-policy/`](./openai-node-tool-policy/) |
| Understand the SDK without any framework | [`custom-tool-policy/`](./custom-tool-policy/) |

All examples:
- Run offline by default — no gateway or API key required
- Use TypeScript strict mode
- Include a deterministic smoke test runnable in CI

## Sub-project layout

Each sub-project follows this structure:

```text
node/<example-name>/
  README.md         ← prerequisites, install, run, expected output, troubleshooting
  package.json      ← pnpm project with build/start/test/typecheck scripts
  tsconfig.json     ← strict TypeScript
  .env.example      ← optional gateway URL and provider keys (not required to run)
  src/
    index.ts        ← entrypoint
    tools.ts        ← tool definitions and mock implementations
    policy.ts       ← allow/deny policy rules
  tests/
    smoke.test.ts   ← vitest smoke test (runs offline)
```

## Back to root

[← Agent Assembly Examples](../README.md)
