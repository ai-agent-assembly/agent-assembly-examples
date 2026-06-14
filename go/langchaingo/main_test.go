package main

import (
	"context"
	"errors"
	"testing"

	"github.com/ai-agent-assembly/go-sdk/assembly"
	"github.com/tmc/langchaingo/llms"
	"github.com/tmc/langchaingo/llms/fake"
	"github.com/tmc/langchaingo/tools"
)

func TestSearchToolReturnsSummary(t *testing.T) {
	t.Parallel()

	result, err := (&searchTool{}).Call(context.Background(), "agents")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "(summary for agents)" {
		t.Fatalf("unexpected result: %q", result)
	}
}

func TestSendEmailToolReturnsSent(t *testing.T) {
	t.Parallel()

	result, err := (&sendEmailTool{}).Call(context.Background(), "a@b.com")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "sent email to a@b.com" {
		t.Fatalf("unexpected result: %q", result)
	}
}

// TestWrappedToolsSatisfyLangChainGoToolInterface proves that an
// assembly-governed tool is still a valid LangChainGo tool — the property
// that makes the integration drop-in.
func TestWrappedToolsSatisfyLangChainGoToolInterface(t *testing.T) {
	t.Parallel()

	governed := assembly.WrapTools([]assembly.Tool{&searchTool{}}, &policyClient{})
	var _ tools.Tool = governed[0]
}

func TestGovernanceAllowsSearch(t *testing.T) {
	t.Parallel()

	governed := assembly.WrapTools([]assembly.Tool{&searchTool{}}, &policyClient{})

	result, err := governed[0].Call(context.Background(), "allowed")
	if err != nil {
		t.Fatalf("expected allowed call, got error: %v", err)
	}
	if result != "(summary for allowed)" {
		t.Fatalf("unexpected result: %q", result)
	}
}

func TestGovernanceDeniesSendEmail(t *testing.T) {
	t.Parallel()

	governed := assembly.WrapTools([]assembly.Tool{&sendEmailTool{}}, &policyClient{})

	_, err := governed[0].Call(context.Background(), "user@example.com")
	if err == nil {
		t.Fatal("expected denied call to return error")
	}

	var pve *assembly.PolicyViolationError
	if !errors.As(err, &pve) {
		t.Fatalf("expected PolicyViolationError, got %T: %v", err, err)
	}
	if pve.ToolName != "send-email" {
		t.Fatalf("expected ToolName %q, got %q", "send-email", pve.ToolName)
	}
	if pve.Reason != "outbound email is blocked by policy" {
		t.Fatalf("unexpected denial reason: %q", pve.Reason)
	}
}

// TestFakeLLMDrivesAgentOffline confirms the LangChainGo model layer runs with
// no API key, keeping the example CI-safe.
func TestFakeLLMDrivesAgentOffline(t *testing.T) {
	t.Parallel()

	model := fake.NewFakeLLM([]string{"search then email"})
	plan, err := llms.GenerateFromSinglePrompt(context.Background(), model, "plan")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if plan != "search then email" {
		t.Fatalf("unexpected plan: %q", plan)
	}
}
