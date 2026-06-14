import { describe, expect, it } from "vitest";
import { PolicyViolationError, withAssembly } from "@agent-assembly/sdk";
import { createPolicyGatewayClient } from "../src/policy.js";
import { getStockPriceTool, placeTradeTool } from "../src/tools.js";

function runTool(
  tool: { execute?: ((inputData: never, context: never) => Promise<unknown>) | undefined },
  input: Record<string, unknown>
): Promise<unknown> {
  if (!tool.execute) throw new Error("tool has no execute function");
  return tool.execute(input as never, {} as never);
}

describe("withAssembly governance over Mastra tools", () => {
  it("allows get_stock_price through the policy gateway client", async () => {
    const tools = withAssembly(
      {
        get_stock_price: {
          execute: async (args: Record<string, unknown>) => runTool(getStockPriceTool, args),
        },
      },
      { gatewayClient: createPolicyGatewayClient() }
    );
    const out = await tools.get_stock_price.execute({ ticker: "AASM" });
    expect(JSON.stringify(out)).toContain("AASM");
  });

  it("blocks place_trade with PolicyViolationError", async () => {
    const tools = withAssembly(
      {
        place_trade: {
          execute: async (args: Record<string, unknown>) => runTool(placeTradeTool, args),
        },
      },
      { gatewayClient: createPolicyGatewayClient() }
    );
    await expect(
      tools.place_trade.execute({ ticker: "AASM", shares: 10 })
    ).rejects.toBeInstanceOf(PolicyViolationError);
  });
});
