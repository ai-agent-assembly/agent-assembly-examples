package main

import (
	"context"
	"errors"
	"fmt"

	"github.com/AI-agent-assembly/go-sdk/assembly"
)

const policyFile = "../policy.yaml"

func main() {
	fmt.Printf("%s\n", repeat("=", 62))
	fmt.Printf("  Agent Assembly — Policy Enforcement Scenario (Go)\n")
	fmt.Printf("%s\n\n", repeat("=", 62))

	cfg, err := loadPolicyConfig(policyFile)
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return
	}

	fmt.Printf("Policy loaded from policy.yaml  (%d rules, default: %s)\n", len(cfg.Rules), cfg.DefaultAction)
	for _, r := range cfg.Rules {
		icon := "ALLOW"
		if r.Action == "deny" {
			icon = "DENY "
		}
		fmt.Printf("  %s  %-14s — %s\n", icon, r.Tool, r.Reason)
	}
	fmt.Println()

	client := newPolicyClient(cfg)
	tools := assembly.WrapTools(
		[]assembly.Tool{
			&readConfigTool{},
			&listAgentsTool{},
			&deleteAgentTool{},
			&sendEmailTool{},
		},
		client,
	)

	inputs := map[string]string{
		"read_config":  "database.host",
		"list_agents":  "",
		"delete_agent": "agent-001",
		"send_email":   "to=admin@example.com subject=Hello",
	}

	fmt.Println("Running governed tool calls:")
	fmt.Printf("%s\n", repeat("-", 44))
	allowed, denied := 0, 0
	for _, tool := range tools {
		input := inputs[tool.Name()]
		fmt.Printf("  → %s(%q)\n", tool.Name(), input)
		result, err := tool.Call(context.Background(), input)
		if err != nil {
			var pve *assembly.PolicyViolationError
			if errors.As(err, &pve) {
				fmt.Printf("     ❌ DENIED   — %v\n", pve)
				denied++
			} else {
				fmt.Printf("     ⚠️  ERROR    — %v\n", err)
			}
		} else {
			fmt.Printf("     ✅ ALLOWED  — %s\n", result)
			allowed++
		}
		fmt.Println()
	}
	fmt.Printf("%d tool calls: %d allowed, %d denied.\n", allowed+denied, allowed, denied)
}

func repeat(s string, n int) string {
	result := ""
	for i := 0; i < n; i++ {
		result += s
	}
	return result
}
