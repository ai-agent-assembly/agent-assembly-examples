# Quick-start snippets (generated)

Per-framework "Govern your first agent" code snippets for each SDK's quick-start
docs (Epic **AAASM-4511**). Everything in this directory except this README is
**generated** — do not edit snippet files or `manifest.json` by hand.

## How it works

Each framework example's entrypoint marks the minimal "init assembly + govern the
agent" slice with a stable region:

```python
# region: quickstart
with init_assembly(...) as ctx:
    ...
# endregion
```

`# region: quickstart` / `# endregion` for Python, `// region: quickstart` /
`// endregion` for TypeScript and Go. `scripts/extract_snippets.py` reads that
slice from every marked entrypoint and writes:

- `snippets/<sdk>/<framework_id>.<ext>` — the dedented snippet, one file per
  example (`<sdk>` ∈ `python` · `node` · `go`).
- `snippets/manifest.json` — the data-driven tab index consumed by the
  python-sdk / node-sdk / go-sdk quick-start tickets.

Because the examples' own `verify-python` / `verify-node` / `verify-go` CI runs
each entrypoint, the extracted region stays runnable. A drift check in
`.github/workflows/example-metadata-check.yml` re-runs the extractor and fails
the PR if the committed snippets or manifest differ from the entrypoints.

## Regenerate

```bash
python scripts/extract_snippets.py
```

## Adding a framework tab

1. Add the example under `python/`, `node/`, or `go/` (as usual).
2. Wrap its govern slice with `region: quickstart` / `endregion` markers.
3. (Optional) Add a nicer label / a `status` in
   `metadata/framework-labels.json`; without an entry the label is derived from
   the directory name and `status` defaults to `validated`.
4. Run `python scripts/extract_snippets.py` and commit the result.

## `manifest.json` schema

```jsonc
{
  "schema_version": 1,
  "generator": "scripts/extract_snippets.py",
  "sdks": {
    "<sdk>": [                         // "python" | "node" | "go"
      {
        "framework_id":   "<slug>",    // example dir name; stable key, unique per sdk
        "label":          "<string>",  // human tab label (e.g. "LangChain")
        "status":         "<string>",  // "validated" (default) | "experimental"
        "lang":           "<string>",  // "python" | "typescript" | "go"
        "snippet_path":   "snippets/<sdk>/<slug>.<ext>",
        "source_example": "<sdk>/<slug>/<entrypoint>"
      }
    ]
  }
}
```

Treat `framework_id` as the stable key and `label` as display text. Entries are
ordered by `framework_id` within each SDK. The curated display metadata (`label`,
`status`) lives in `metadata/framework-labels.json`; the snippet content and all
paths are derived from the runnable examples.
