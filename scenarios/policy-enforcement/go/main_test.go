package main

import (
	"context"
	"errors"
	"testing"

	"github.com/AI-agent-assembly/go-sdk/assembly"
)

const testPolicyFile = "../policy.yaml"

func loadTestClient(t *testing.T) *policyClient {
	t.Helper()
	cfg, err := loadPolicyConfig(testPolicyFile)
	if err != nil {
		t.Fatalf("loadPolicyConfig: %v", err)
	}
	return newPolicyClient(cfg)
}

func TestReadConfigIsAllowed(t *testing.T) {
	t.Parallel()
	client := loadTestClient(t)
	tools := assembly.WrapTools([]assembly.Tool{&readConfigTool{}}, client)

	result, err := tools[0].Call(context.Background(), "database.host")
	if err != nil {
		t.Fatalf("expected allowed, got error: %v", err)
	}
	if result != "localhost:5432" {
		t.Fatalf("unexpected result: %q", result)
	}
}

func TestListAgentsIsAllowed(t *testing.T) {
	t.Parallel()
	client := loadTestClient(t)
	tools := assembly.WrapTools([]assembly.Tool{&listAgentsTool{}}, client)

	result, err := tools[0].Call(context.Background(), "")
	if err != nil {
		t.Fatalf("expected allowed, got error: %v", err)
	}
	if result == "" {
		t.Fatal("expected non-empty agent list")
	}
}

func TestDeleteAgentIsDenied(t *testing.T) {
	t.Parallel()
	client := loadTestClient(t)
	tools := assembly.WrapTools([]assembly.Tool{&deleteAgentTool{}}, client)

	_, err := tools[0].Call(context.Background(), "agent-001")
	if err == nil {
		t.Fatal("expected denial error, got nil")
	}
	var pve *assembly.PolicyViolationError
	if !errors.As(err, &pve) {
		t.Fatalf("expected PolicyViolationError, got %T: %v", err, err)
	}
	if pve.ToolName != "delete_agent" {
		t.Fatalf("expected ToolName %q, got %q", "delete_agent", pve.ToolName)
	}
}

func TestSendEmailIsDenied(t *testing.T) {
	t.Parallel()
	client := loadTestClient(t)
	tools := assembly.WrapTools([]assembly.Tool{&sendEmailTool{}}, client)

	_, err := tools[0].Call(context.Background(), "admin@example.com")
	if err == nil {
		t.Fatal("expected denial error, got nil")
	}
	var pve *assembly.PolicyViolationError
	if !errors.As(err, &pve) {
		t.Fatalf("expected PolicyViolationError, got %T: %v", err, err)
	}
}

func TestUnknownToolIsDeniedByDefault(t *testing.T) {
	t.Parallel()
	client := loadTestClient(t)

	stubTool := &namedStub{name: "execute_shell"}
	tools := assembly.WrapTools([]assembly.Tool{stubTool}, client)

	_, err := tools[0].Call(context.Background(), "rm -rf /")
	if err == nil {
		t.Fatal("expected default-deny for unknown tool, got nil")
	}
	var pve *assembly.PolicyViolationError
	if !errors.As(err, &pve) {
		t.Fatalf("expected PolicyViolationError, got %T: %v", err, err)
	}
}

func TestLoadPolicyConfigRules(t *testing.T) {
	t.Parallel()
	cfg, err := loadPolicyConfig(testPolicyFile)
	if err != nil {
		t.Fatalf("loadPolicyConfig: %v", err)
	}
	if len(cfg.Rules) < 4 {
		t.Fatalf("expected at least 4 rules, got %d", len(cfg.Rules))
	}
	if cfg.DefaultAction != "deny" {
		t.Fatalf("expected default_action=deny, got %q", cfg.DefaultAction)
	}
}

// namedStub is a stub tool that always returns "ok" when called.
type namedStub struct{ name string }

func (n *namedStub) Name() string                                     { return n.name }
func (n *namedStub) Description() string                              { return "stub" }
func (n *namedStub) Call(_ context.Context, _ string) (string, error) { return "ok", nil }
