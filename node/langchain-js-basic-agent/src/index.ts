import { initAssembly } from "@agent-assembly/sdk";
import { evaluate } from "./policy.js";
import { TOOLS, type ToolName } from "./tools.js";

async function runTool(toolName: ToolName, args: Record<string, unknown>): Promise<void> {
  const rule = evaluate(toolName);
  if (rule.action === "deny") {
    console.log(`[POLICY DENY] ${toolName}: ${rule.reason}`);
    return;
  }
  const result = TOOLS[toolName](args);
  console.log(`[POLICY ALLOW] ${toolName}: ${result.output}`);
}

async function main(): Promise<void> {
  console.log("=== LangChain.js-style Agent Assembly Example ===\n");

  const _ctx = await initAssembly({
    agentId: "langchain-js-example-agent",
    mode: "auto",
  });

  console.log("Running allowed tool: get_weather");
  await runTool("get_weather", { location: "Taipei" });

  console.log("\nRunning denied tool: delete_file");
  await runTool("delete_file", { path: "/etc/hosts" });

  console.log("\nDone. Tool calls governed by the local policy.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
