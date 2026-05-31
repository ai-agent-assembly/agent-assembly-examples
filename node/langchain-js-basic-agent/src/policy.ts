export interface PolicyRule {
  tool: string;
  action: "allow" | "deny";
  reason: string;
}

export const POLICY_RULES: PolicyRule[] = [
  {
    tool: "get_weather",
    action: "allow",
    reason: "Read-only external data lookup — safe to execute.",
  },
  {
    tool: "delete_file",
    action: "deny",
    reason: "Destructive filesystem operations require human approval.",
  },
];

export function evaluate(toolName: string): PolicyRule {
  const rule = POLICY_RULES.find((r) => r.tool === toolName);
  if (rule) return rule;
  return { tool: toolName, action: "deny", reason: "No policy rule found — deny by default." };
}
