import { describe, expect, it } from "vitest";
import { PolicyViolationError, withAssembly } from "@agent-assembly/sdk";
import { createPolicyGatewayClient } from "../src/policy.js";

describe("withAssembly governance", () => {
  it("allows get_weather through the policy gateway client", async () => {
    const tools = withAssembly(
      { get_weather: { execute: async () => "ran" } },
      { gatewayClient: createPolicyGatewayClient() }
    );
    expect(await tools.get_weather.execute()).toBe("ran");
  });

  it("blocks delete_file with PolicyViolationError", async () => {
    const tools = withAssembly(
      { delete_file: { execute: async () => "ran" } },
      { gatewayClient: createPolicyGatewayClient() }
    );
    await expect(tools.delete_file.execute()).rejects.toBeInstanceOf(PolicyViolationError);
  });
});
