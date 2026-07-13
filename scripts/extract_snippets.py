#!/usr/bin/env python3
"""Extract per-framework quick-start snippets from the runnable examples.

WHY THIS EXISTS
---------------
Each SDK's quick-start "Govern your first agent" step (AAASM-4511) shows one tab
per supported agent framework, and every tab's snippet must be a *slice of a
runnable example* — not a hand-maintained copy that silently rots (the
AAASM-4451 stale-sample class). This script is the single extraction point that
keeps the doc snippets in lockstep with the examples: it reads the marked
``region: quickstart`` slice from each framework entrypoint and emits

  * ``snippets/<sdk>/<framework_id>.<ext>`` — one snippet file per example, and
  * ``snippets/manifest.json`` — the data-driven tab index the python-sdk /
    node-sdk / go-sdk quick-start tickets consume.

Because the examples' own ``verify-*`` CI already runs each entrypoint, the
extracted region stays runnable with no new execution lane. A CI drift check
(``.github/workflows/example-metadata-check.yml``) re-runs this script and fails
if the committed snippets/manifest differ from what the entrypoints produce, so
a snippet can never drift from the example it was cut from.

DESIGN CONSTRAINTS (mirrors ``generate_example_metadata.py``)
-------------------------------------------------------------
* Standard library only — no third-party parser — so the CI drift check needs no
  install step and runs on any CI Python.
* Idempotent: running twice produces no diff. This is a hard requirement the
  drift check enforces.
* Data-driven discovery: the framework list is the set of example directories
  that carry a ``region: quickstart`` marker, so a framework added later appears
  automatically once its entrypoint is marked — nothing here is hard-coded to a
  fixed framework list.
* Display metadata (human label, validation status) is the only curated input,
  and it is optional: ``metadata/framework-labels.json`` overrides the default
  label/status per example. A new example with no registry entry still appears,
  with a label derived from its directory name.

MANIFEST SCHEMA (``snippets/manifest.json``) — the contract for the SDK tickets
-------------------------------------------------------------------------------
::

    {
      "schema_version": 1,
      "generator": "scripts/extract_snippets.py",
      "sdks": {
        "<sdk>": [                       # sdk ∈ {"python", "node", "go"}
          {
            "framework_id":   "<slug>",  # example dir name; stable, unique per sdk
            "label":          "<str>",   # human tab label (LangChain, Pydantic AI, …)
            "status":         "<str>",   # "validated" (default) | "experimental"
            "lang":           "<str>",   # "python" | "typescript" | "go"
            "snippet_path":   "snippets/<sdk>/<slug>.<ext>",
            "source_example": "<sdk>/<slug>/<entrypoint>"
          },
          ...
        ]
      }
    }

Consumers should treat ``framework_id`` as the stable key and ``label`` as
display text. Entries are ordered by ``framework_id`` within each SDK.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 1
GENERATOR = "scripts/extract_snippets.py"

# Region markers. The begin marker opens the "init assembly + govern the agent"
# slice; the end marker closes it. Both are plain comments so they never change
# example behavior, and both comment styles (``#`` for Python, ``//`` for TS/Go)
# are accepted so one regex serves every SDK.
_BEGIN_RE = re.compile(r"^\s*(?:#|//)\s*region:\s*quickstart\b")
_END_RE = re.compile(r"^\s*(?:#|//)\s*endregion\b")


@dataclass(frozen=True)
class SdkSpec:
    """One SDK's discovery + emission shape."""

    key: str  # manifest key / snippets subdir: "python" | "node" | "go"
    entrypoint: str  # entrypoint path relative to an example dir
    ext: str  # snippet file extension, including the dot
    lang: str  # manifest ``lang`` value


# The examples' entrypoint conventions (see scripts/discover_samples.py): Python
# uses ``src/main.py``, Node ``src/index.ts``, Go ``main.go``.
SDKS: tuple[SdkSpec, ...] = (
    SdkSpec(key="python", entrypoint="src/main.py", ext=".py", lang="python"),
    SdkSpec(key="node", entrypoint="src/index.ts", ext=".ts", lang="typescript"),
    SdkSpec(key="go", entrypoint="main.go", ext=".go", lang="go"),
)


class SnippetError(RuntimeError):
    """A malformed or missing region marker in a marked entrypoint."""


# ---------------------------------------------------------------------------
# Region extraction
# ---------------------------------------------------------------------------


def _dedent(body: list[str]) -> list[str]:
    """Strip surrounding blank lines and the common leading indentation.

    Whitespace is counted per character, so a Go region indented with one tab is
    dedented by one tab and a Python region indented with four spaces by four —
    the source file keeps its own indentation; only the extracted copy is
    normalized for display.
    """

    lines = list(body)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return []
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    common = min(indents) if indents else 0
    return [ln[common:] if ln.strip() else "" for ln in lines]


def has_region(text: str) -> bool:
    """True if *text* opens a ``region: quickstart`` marker."""

    return any(_BEGIN_RE.match(line) for line in text.splitlines())


def extract_snippet(text: str, source_rel: str) -> str:
    """Return the dedented ``region: quickstart`` slice of *text*.

    Raises :class:`SnippetError` if the begin/end markers are missing, doubled,
    or out of order — a half-added marker must fail the drift check loudly
    rather than silently emit an empty or truncated snippet.
    """

    lines = text.splitlines()
    begins = [i for i, ln in enumerate(lines) if _BEGIN_RE.match(ln)]
    ends = [i for i, ln in enumerate(lines) if _END_RE.match(ln)]
    if len(begins) != 1 or len(ends) != 1:
        raise SnippetError(
            f"{source_rel}: expected exactly one 'region: quickstart' and one "
            f"'endregion' marker, found {len(begins)} begin / {len(ends)} end"
        )
    begin, end = begins[0], ends[0]
    if end <= begin:
        raise SnippetError(f"{source_rel}: 'endregion' precedes 'region: quickstart'")
    body = _dedent(lines[begin + 1 : end])
    if not body:
        raise SnippetError(f"{source_rel}: 'region: quickstart' slice is empty")
    return "\n".join(body) + "\n"


# ---------------------------------------------------------------------------
# Discovery + registry
# ---------------------------------------------------------------------------


def discover(repo_root: Path, spec: SdkSpec) -> list[tuple[str, Path]]:
    """Return ``(framework_id, entrypoint_path)`` for each marked example dir.

    ``framework_id`` is the example directory name. Only directories whose
    entrypoint carries a region marker are returned, so the framework list is
    exactly the set of marked examples — data-driven, no hard-coded roster.
    """

    base = repo_root / spec.key
    found: list[tuple[str, Path]] = []
    if not base.is_dir():
        return found
    for sub in sorted(base.iterdir()):
        if not sub.is_dir():
            continue
        entry = sub / spec.entrypoint
        if entry.is_file() and has_region(entry.read_text(encoding="utf-8")):
            found.append((sub.name, entry))
    return found


def load_labels(repo_root: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Load the optional ``metadata/framework-labels.json`` display registry.

    Shape: ``{sdk: {framework_id: {"label": str, "status": str}}}``. Missing file
    or missing entries fall back to derived defaults, so the registry is purely
    optional polish and never gates discovery.
    """

    path = repo_root / "metadata" / "framework-labels.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SnippetError("metadata/framework-labels.json must be a JSON object")
    return data


def derive_label(framework_id: str) -> str:
    """Best-effort human label for an example dir with no registry entry."""

    words = framework_id.replace("_", "-").split("-")
    return " ".join(word.capitalize() for word in words if word)


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------


def _write_if_changed(path: Path, text: str) -> bool:
    """Write *text* to *path* iff it differs. Returns True when rewritten."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def _prune_orphans(sdk_dir: Path, ext: str, keep: set[str]) -> list[Path]:
    """Delete snippet files under *sdk_dir* whose stem is not in *keep*.

    Keeps ``snippets/<sdk>/`` an exact mirror of the marked examples so a renamed
    or removed example leaves no stale snippet the drift check would miss.
    """

    removed: list[Path] = []
    if not sdk_dir.is_dir():
        return removed
    for existing in sorted(sdk_dir.glob(f"*{ext}")):
        if existing.stem not in keep:
            existing.unlink()
            removed.append(existing)
    return removed


def build(repo_root: Path) -> tuple[dict, list[Path]]:
    """Extract every snippet, write the files, and return ``(manifest, changed)``."""

    labels = load_labels(repo_root)
    snippets_root = repo_root / "snippets"
    changed: list[Path] = []
    manifest: dict = {
        "schema_version": SCHEMA_VERSION,
        "generator": GENERATOR,
        "sdks": {},
    }

    for spec in SDKS:
        entries: list[dict[str, str]] = []
        slugs: set[str] = set()
        for framework_id, entry_path in discover(repo_root, spec):
            source_rel = entry_path.relative_to(repo_root).as_posix()
            snippet = extract_snippet(
                entry_path.read_text(encoding="utf-8"), source_rel
            )
            snippet_rel = f"snippets/{spec.key}/{framework_id}{spec.ext}"
            if _write_if_changed(repo_root / snippet_rel, snippet):
                changed.append(repo_root / snippet_rel)
            slugs.add(framework_id)

            registry = labels.get(spec.key, {}).get(framework_id, {})
            entries.append(
                {
                    "framework_id": framework_id,
                    "label": registry.get("label") or derive_label(framework_id),
                    "status": registry.get("status") or "validated",
                    "lang": spec.lang,
                    "snippet_path": snippet_rel,
                    "source_example": source_rel,
                }
            )

        changed.extend(_prune_orphans(snippets_root / spec.key, spec.ext, slugs))
        manifest["sdks"][spec.key] = entries

    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if _write_if_changed(snippets_root / "manifest.json", manifest_text):
        changed.append(snippets_root / "manifest.json")
    return manifest, changed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _repo_root_from_script() -> Path:
    # This file lives at <repo>/scripts/extract_snippets.py.
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_repo_root_from_script(),
        help="Path to the repository root (defaults to the script's parent).",
    )
    args = parser.parse_args(argv)

    try:
        manifest, changed = build(args.repo_root)
    except SnippetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    total = sum(len(v) for v in manifest["sdks"].values())
    print(f"Extracted {total} snippet(s) across {len(manifest['sdks'])} SDK(s).")
    if changed:
        print(f"Rewrote {len(changed)} file(s):")
        for path in sorted(changed):
            print(f"  {path.relative_to(args.repo_root)}")
    else:
        print("No changes — snippets and manifest already match the entrypoints.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
