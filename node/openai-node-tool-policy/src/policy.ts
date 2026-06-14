import type { GatewayClient } from "@agent-assembly/sdk";

export interface PolicyRule {
  tool: string;
  action: "allow" | "deny";
  reason: string;
}

export const POLICY_RULES: PolicyRule[] = [
  {
    tool: "search_web",
    action: "allow",
    reason: "Read-only search — safe to execute without approval.",
  },
  {
    tool: "send_email",
    action: "deny",
    reason: "External communication requires human approval before sending.",
  },
];

export function evaluate(toolName: string): PolicyRule {
  const rule = POLICY_RULES.find((r) => r.tool === toolName);
  if (rule) return rule;
  return { tool: toolName, action: "deny", reason: "No matching policy rule — deny by default." };
}

/**
 * Build a GatewayClient that enforces this example's local policy in-process,
 * so withAssembly can govern tool calls offline — no running gateway required.
 */
export function createPolicyGatewayClient(): GatewayClient {
  return {
    mode: "sdk-only",
    start: async () => undefined,
    close: async () => undefined,
    check: async (request) => {
      const rule = evaluate(request.toolName ?? "");
      return rule.action === "deny"
        ? { denied: true, reason: rule.reason }
        : { denied: false };
    },
    waitForApproval: async () => ({ denied: false }),
    record: async () => undefined,
    recordResult: async () => undefined,
    scanPrompts: async () => undefined
  };
}
