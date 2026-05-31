package main

import (
	"context"
	"fmt"
	"os"

	"github.com/AI-agent-assembly/go-sdk/assembly"
	"gopkg.in/yaml.v3"
)

// policyRule mirrors a rule in policy.yaml.
type policyRule struct {
	Tool   string `yaml:"tool"`
	Action string `yaml:"action"`
	Reason string `yaml:"reason"`
}

// policyConfig is the top-level policy.yaml structure.
type policyConfig struct {
	Rules         []policyRule `yaml:"rules"`
	DefaultAction string       `yaml:"default_action"`
	DefaultReason string       `yaml:"default_reason"`
}

// loadPolicyConfig reads and parses ../policy.yaml relative to the working directory.
func loadPolicyConfig(path string) (*policyConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read policy file: %w", err)
	}
	var cfg policyConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("parse policy file: %w", err)
	}
	return &cfg, nil
}

// policyClient enforces per-tool allow/deny rules loaded from policy.yaml.
// It implements assembly.GovernanceClient.
type policyClient struct {
	rules         map[string]policyRule
	defaultAction string
	defaultReason string
}

func newPolicyClient(cfg *policyConfig) *policyClient {
	rules := make(map[string]policyRule, len(cfg.Rules))
	for _, r := range cfg.Rules {
		rules[r.Tool] = r
	}
	return &policyClient{
		rules:         rules,
		defaultAction: cfg.DefaultAction,
		defaultReason: cfg.DefaultReason,
	}
}

func (p *policyClient) Check(_ context.Context, req assembly.CheckRequest) (assembly.Decision, error) {
	if rule, ok := p.rules[req.ToolName]; ok {
		if rule.Action == "deny" {
			fmt.Printf("[policy] DENIED   tool=%s  reason=%q\n", req.ToolName, rule.Reason)
			return assembly.Decision{Denied: true, Reason: rule.Reason}, nil
		}
		fmt.Printf("[policy] ALLOWED  tool=%s\n", req.ToolName)
		return assembly.Decision{Denied: false}, nil
	}
	// Default: deny unknown tools (fail-closed).
	fmt.Printf("[policy] DENIED   tool=%s  reason=%q\n", req.ToolName, p.defaultReason)
	return assembly.Decision{Denied: true, Reason: p.defaultReason}, nil
}

func (p *policyClient) WaitForApproval(_ context.Context, _ assembly.ApprovalRequest) (assembly.Decision, error) {
	return assembly.Decision{Denied: false}, nil
}

func (p *policyClient) RecordResult(_ context.Context, _ assembly.RecordRequest) error { return nil }
func (p *policyClient) Close() error                                                    { return nil }
