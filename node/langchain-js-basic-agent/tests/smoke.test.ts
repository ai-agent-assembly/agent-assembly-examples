import { describe, expect, it } from "vitest";
import { evaluate } from "../src/policy.js";
import { TOOLS } from "../src/tools.js";

describe("policy", () => {
  it("allows get_weather", () => {
    const rule = evaluate("get_weather");
    expect(rule.action).toBe("allow");
  });

  it("denies delete_file", () => {
    const rule = evaluate("delete_file");
    expect(rule.action).toBe("deny");
  });

  it("denies unknown tools by default", () => {
    const rule = evaluate("unknown_tool");
    expect(rule.action).toBe("deny");
  });
});

describe("tools", () => {
  it("get_weather returns mock weather output", () => {
    const result = TOOLS.get_weather({ location: "Taipei" });
    expect(result.allowed).toBe(true);
    expect(result.output).toContain("Taipei");
  });

  it("delete_file returns blocked output", () => {
    const result = TOOLS.delete_file({ path: "/etc/hosts" });
    expect(result.allowed).toBe(false);
    expect(result.output).toContain("BLOCKED");
  });
});
