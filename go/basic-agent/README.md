# basic-agent

Minimal Go example showing how to initialize the Agent Assembly Go SDK and execute a governed tool call.

## What this example demonstrates

- Importing and initializing the Agent Assembly Go SDK
- Defining a tool that satisfies the `assembly.Tool` interface
- Wrapping a tool with `assembly.WrapTools` for governance interception
- Observing the allow decision path through console output
- Using an offline mock `GovernanceClient` for local development and CI

## Prerequisites

| Requirement | Version |
|---|---|
| Go | >= 1.26 |
| Agent Assembly Go SDK | v0.0.1-alpha.2 |

A live Agent Assembly gateway is **not required** to run this example. It uses an
offline mock `GovernanceClient` by default. Set `ASSEMBLY_GATEWAY_URL` and
`ASSEMBLY_API_KEY` to connect to a real gateway.

## Setup

```bash
git clone https://github.com/ai-agent-assembly/agent-assembly-examples.git
cd agent-assembly-examples/go/basic-agent
go mod download
```

## Run

```bash
go run .
```

### With a real gateway

```bash
export ASSEMBLY_GATEWAY_URL=https://your-gateway.example.com
export ASSEMBLY_API_KEY=your-api-key
go run .
```

## Expected output (offline mock)

```text
[assembly] no gateway configured — using offline mock governance client
[assembly] governance: ALLOWED  tool=echo input="Hello, Agent Assembly!"
[assembly] tool result: Hello, Agent Assembly!
```

## Test

```bash
go test ./...
```

Tests run entirely offline using the mock client — no gateway required.

## How it works

1. An `echoTool` implements `assembly.Tool` (Name, Description, Call).
2. `assembly.WrapTools` wraps the tool with a `GovernanceClient`.
3. Before each `Call`, the wrapper sends a `CheckRequest` to the client.
4. The client returns a `Decision` (allowed or denied).
5. Allowed calls proceed to the inner tool; denied calls return `PolicyViolationError`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `go: module github.com/AI-agent-assembly/go-sdk: not found` | Run `go mod download` or check network access to `proxy.golang.org`. |
| `init requires a running sidecar` | Only occurs when using `assembly.Init()` with an explicit gateway URL. This example avoids `Init()` — ignore if using mock mode. |
| Unexpected denial | Check that `ASSEMBLY_GATEWAY_URL` is not set to an endpoint that has deny policies for the `echo` tool. |

## Go SDK docs

- Module: [`github.com/AI-agent-assembly/go-sdk`](https://pkg.go.dev/github.com/AI-agent-assembly/go-sdk)
- `assembly.Tool` interface
- `assembly.WrapTools` function
- `assembly.GovernanceClient` interface

## Back to Go examples

[← Go Examples](../README.md)
