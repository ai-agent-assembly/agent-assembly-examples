import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Tools defined with Mastra's `createTool`.
 *
 * Each tool returns mock output so the example runs fully offline — no provider
 * key and no live LLM are required. `withAssembly` (in index.ts) wraps each
 * tool's `execute` to enforce the local policy before it runs.
 */
export const getStockPriceTool = createTool({
  id: "get_stock_price",
  description: "Look up the latest price for a stock ticker.",
  inputSchema: z.object({ ticker: z.string() }),
  outputSchema: z.object({ text: z.string() }),
  execute: async ({ ticker }) => ({
    text: `${ticker}: $123.45 [mock]`,
  }),
});

export const placeTradeTool = createTool({
  id: "place_trade",
  description: "Place a buy or sell order for a stock ticker.",
  inputSchema: z.object({ ticker: z.string(), shares: z.number() }),
  outputSchema: z.object({ text: z.string() }),
  execute: async ({ ticker, shares }) => ({
    text: `Placed order: ${shares} shares of ${ticker} [mock]`,
  }),
});
