# Go Examples

This directory contains runnable Go examples showing how to integrate Agent Assembly with Go-based AI agent applications.

## What lives here

| Sub-project (coming soon)          | What it demonstrates                                            |
|------------------------------------|-----------------------------------------------------------------|
| `basic-agent/`                     | Build a basic governed agent using the Agent Assembly Go SDK    |
| `tool-policy/`                     | Enforce tool-level allow/deny policies in Go                    |
| `cli-runtime-integration/`         | Integrate the `aasm` CLI runtime into a Go agent workflow       |

All examples use the `github.com/agent-assembly/go-sdk` Go module.

## Prerequisites

- Go >= 1.22
- A running Agent Assembly gateway (see the sub-project README for local dev options)

## Expected sub-project structure

Each sub-project in this directory should follow this layout:

```text
go/<example-name>/
  README.md         ← prerequisites, setup, run, expected output, troubleshooting
  .env.example      ← template for any required secrets or config (never .env)
  go.mod
  go.sum
  main.go           ← entrypoint
```

## Back to root

[← Agent Assembly Examples](../README.md)
