# Node.js / TypeScript Examples

This directory contains runnable Node.js and TypeScript examples showing how to integrate Agent Assembly with popular JavaScript AI agent frameworks.

## What lives here

| Sub-project (coming soon)          | Framework           | What it demonstrates                                         |
|------------------------------------|---------------------|--------------------------------------------------------------|
| `langchain-js-basic-agent/`        | LangChain.js        | Wire Agent Assembly SDK into a basic LangChain.js agent      |
| `openai-node-tool-policy/`         | OpenAI Node SDK     | Enforce tool policies with the OpenAI Node.js SDK            |
| `custom-tool-policy/`              | —                   | Write a custom TypeScript tool wrapper with the SDK          |

All examples use the `@agent-assembly/sdk` npm package.

## Prerequisites

- Node.js >= 20 LTS
- `pnpm` (install via `npm install -g pnpm`)
- A running Agent Assembly gateway (see the sub-project README for local dev options)

## Expected sub-project structure

Each sub-project in this directory should follow this layout:

```text
node/<example-name>/
  README.md         ← prerequisites, setup, run, expected output, troubleshooting
  .env.example      ← template for any required secrets or config (never .env)
  package.json
  tsconfig.json
  src/
    index.ts        ← entrypoint
```

## Back to root

[← Agent Assembly Examples](../README.md)
