export interface ToolResult {
  allowed: boolean;
  output: string;
}

export function readConfig(key: string): ToolResult {
  const config: Record<string, string> = {
    "database.host": "localhost:5432",
    "service.port": "8080",
    "log.level": "INFO",
  };
  const value = config[key] ?? `(no value for '${key}')`;
  return { allowed: true, output: value };
}

export function listAgents(): ToolResult {
  return { allowed: true, output: JSON.stringify(["agent-001", "agent-002", "agent-003"]) };
}

export function deleteAgent(agentId: string): ToolResult {
  return { allowed: true, output: `Deleted agent ${agentId}` };
}

export function sendEmail(to: string, subject: string, body: string): ToolResult {
  return { allowed: true, output: `Email sent to ${to}: ${subject} — ${body}` };
}
