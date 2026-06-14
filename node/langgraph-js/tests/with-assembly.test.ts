import { describe, expect, it } from "vitest";
import { PolicyViolationError, withAssembly } from "@agent-assembly/sdk";
import { createPolicyGatewayClient } from "../src/policy.js";

describe("withAssembly governance over graph-node tools", () => {
  it("allows search_docs through the policy gateway client", async () => {
    const tools = withAssembly(
      { search_docs: { execute: async () => "ran" } },
      { gatewayClient: createPolicyGatewayClient() }
    );
    expect(await tools.search_docs.execute()).toBe("ran");
  });

  it("blocks execute_shell with PolicyViolationError", async () => {
    const tools = withAssembly(
      { execute_shell: { execute: async () => "ran" } },
      { gatewayClient: createPolicyGatewayClient() }
    );
    await expect(tools.execute_shell.execute()).rejects.toBeInstanceOf(PolicyViolationError);
  });
});
