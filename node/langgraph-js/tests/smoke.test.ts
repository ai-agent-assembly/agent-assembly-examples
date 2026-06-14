import { describe, expect, it } from "vitest";
import { evaluate } from "../src/policy.js";
import { searchDocs, executeShell } from "../src/tools.js";
import { END, StateGraph } from "../src/graph.js";

describe("policy", () => {
  it("allows search_docs", () => {
    expect(evaluate("search_docs").action).toBe("allow");
  });

  it("denies execute_shell", () => {
    expect(evaluate("execute_shell").action).toBe("deny");
  });

  it("denies any unlisted tool", () => {
    expect(evaluate("delete_db").action).toBe("deny");
  });
});

describe("tools", () => {
  it("searchDocs returns allowed result with query in output", () => {
    const result = searchDocs("governance");
    expect(result.allowed).toBe(true);
    expect(result.output).toContain("governance");
  });

  it("executeShell returns blocked result", () => {
    const result = executeShell("rm -rf /");
    expect(result.allowed).toBe(false);
    expect(result.output).toContain("BLOCKED");
  });
});

describe("state graph", () => {
  it("runs nodes in edge order from the entry point", async () => {
    const graph = new StateGraph<{ steps: string[] }>()
      .addNode("a", async (s) => ({ steps: [...s.steps, "a"] }))
      .addNode("b", async (s) => ({ steps: [...s.steps, "b"] }))
      .setEntryPoint("a")
      .addEdge("a", "b")
      .addEdge("b", END)
      .compile();

    const out = await graph.invoke({ steps: [] });
    expect(out.steps).toEqual(["a", "b"]);
  });
});
