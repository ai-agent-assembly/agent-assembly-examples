/**
 * A minimal LangGraph.js-style state machine.
 *
 * The real `@langchain/langgraph` package transitively installs `@langchain/core`,
 * which these non-LangChain examples deliberately avoid so they run offline in CI.
 * This file replays the same shape — a typed state, named nodes, and edges between
 * them — so the example reads like a LangGraph.js graph while staying dependency-free.
 * Tool calls inside nodes are governed by `withAssembly` (see index.ts).
 */

export const END = "__end__" as const;

export type NodeFn<TState> = (state: TState) => Promise<TState>;

export class StateGraph<TState> {
  private readonly nodes = new Map<string, NodeFn<TState>>();
  private readonly edges = new Map<string, string>();
  private entry: string | undefined;

  addNode(name: string, fn: NodeFn<TState>): this {
    this.nodes.set(name, fn);
    return this;
  }

  setEntryPoint(name: string): this {
    this.entry = name;
    return this;
  }

  addEdge(from: string, to: string): this {
    this.edges.set(from, to);
    return this;
  }

  compile(): CompiledGraph<TState> {
    if (!this.entry) {
      throw new Error("StateGraph: entry point not set");
    }
    return new CompiledGraph<TState>(this.nodes, this.edges, this.entry);
  }
}

export class CompiledGraph<TState> {
  constructor(
    private readonly nodes: Map<string, NodeFn<TState>>,
    private readonly edges: Map<string, string>,
    private readonly entry: string
  ) {}

  async invoke(initialState: TState): Promise<TState> {
    let current: string | undefined = this.entry;
    let state = initialState;

    while (current && current !== END) {
      const node = this.nodes.get(current);
      if (!node) {
        throw new Error(`StateGraph: node "${current}" not found`);
      }
      state = await node(state);
      current = this.edges.get(current);
    }

    return state;
  }
}
