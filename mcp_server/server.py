#!/usr/bin/env python3
"""
Hollow Attractor MCP Server

Exposes Hollow Attractor filesystem and git operations to Claude via the Model Context
Protocol. This server is a thin I/O layer — all protocol logic lives in the system
prompt. The server reads and writes ~/.hollow-attractor files and runs git.

Usage:
    python3 server.py              # runs via stdio (Claude Desktop)
    python3 server.py --test       # smoke-tests all tools against ~/.hollow-attractor
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── Configuration ─────────────────────────────────────────────────────────────
# ROOT_DIR can be overridden via environment variable for testing:
#   HOLLOW_DIR=/tmp/hollow-test python3 server.py --test

ROOT_DIR          = Path(os.environ.get("HOLLOW_DIR", str(Path.home() / ".hollow-attractor")))
ATTRACTOR_DIR     = ROOT_DIR / "attractor"
WORLDLINES_DIR    = ROOT_DIR / "worldlines"
DIVERGENCES_DIR   = ATTRACTOR_DIR / "divergences"
BACKUP_DIR        = Path(os.environ.get("HOLLOW_BACKUP_DIR", str(Path.home() / "hollow-backups")))

# SYSTEM_PROMPT.md: bundled inside the package when pip-installed,
# or at the repo root when running from source.
_pkg_data_prompt  = Path(__file__).parent / "SYSTEM_PROMPT.md"
_repo_root_prompt = Path(__file__).parent.parent / "SYSTEM_PROMPT.md"
SYSTEM_PROMPT_PATH = _pkg_data_prompt if _pkg_data_prompt.exists() else _repo_root_prompt

mcp = FastMCP(
    "hollow-attractor",
    instructions=(
        "Hollow Attractor memory and task protocol. "
        "Provides read/write access to ~/.hollow-attractor worldline state, "
        "the Ship Log, divergences, archives, and git commits."
    ),
)

# Set serverInfo.version to the hollow-attractor package version.
# FastMCP defaults to the mcp library version, which is misleading in diagnostics.
try:
    from importlib.metadata import version as _pkg_version
    mcp._mcp_server.version = _pkg_version("hollow-attractor")
except Exception:
    pass

# Suppress outputSchema on all tools. FastMCP 1.x emits outputSchema
# unconditionally based on return type annotations, but outputSchema is only
# defined in the MCP 2025-03-26 spec. Clients negotiating 2024-11-05 (including
# Claude Code) may silently discard the entire tools/list response when they
# encounter it. Setting structured_output=False prevents the field from being
# emitted regardless of return annotation.
def tool(fn=None, **kwargs):
    kwargs.setdefault("structured_output", False)
    if fn is not None:
        return mcp.tool(**kwargs)(fn)
    return mcp.tool(**kwargs)

# ── Internal helpers ──────────────────────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()


def _worldline_dir(slug: str) -> Path:
    return WORLDLINES_DIR / slug


def _check_initialized() -> str | None:
    """Returns an error string if not initialized, else None."""
    if not (ROOT_DIR / ".git").exists():
        return "ERROR: ~/.hollow-attractor is not initialized. Run hollow-init.sh first."
    return None


def _read(path: Path) -> str:
    if not path.exists():
        return f"ERROR: file not found: {path}"
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> str:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        # Remove .gitkeep placeholder from parent if present — it is no longer
        # needed once a real file exists in the directory.
        gitkeep = path.parent / ".gitkeep"
        if gitkeep.exists():
            gitkeep.unlink()
        return "ok"
    except OSError as exc:
        return f"ERROR: {exc}"


def _git(*args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT_DIR), *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


# ── Worldline state template ──────────────────────────────────────────────────

def _state_template(slug: str, today: str) -> str:
    return f"""\
# Worldline: {slug}
created: {today}
okr: []
last_anneal: null
last_updated: {today}

## Summary
(not yet written)

## Current Focus
(not yet set)

## Open Questions
(none)

## Key Decisions
(none)

## References
(none)

## Ingestion Log
(none)

## Divergences
(none)
"""


def _items_template(slug: str, today: str) -> str:
    return f"""\
# Items: {slug}
last_updated: {today}

## Inbox
(none)

## Actionable
(none)

## Waiting
(none)

## Completed
(none)
"""


def _archive_recent_template(slug: str, today: str) -> str:
    return f"""\
# Archive — Recent (last 7 days): {slug}
last_updated: {today}

(none)
"""


def _prefs_template() -> str:
    return """\
# Per-worldline preferences — all fields optional, override global
# anneal_threshold_days: 14
# stale_question_days: 21
"""


# ── Read tools ────────────────────────────────────────────────────────────────

@tool()
def read_ship_log() -> str:
    """Read the Hollow Attractor Ship Log (global cross-session index).
    Call this at the start of every session before any other operation."""
    if err := _check_initialized():
        return err
    return _read(ATTRACTOR_DIR / "ship-log.md")


@tool()
def read_worldline(slug: str) -> str:
    """Read state.md and items.md for a worldline, concatenated with a separator.

    slug: worldline directory name (e.g. 'work-projectx')
    """
    if err := _check_initialized():
        return err
    wl_dir = _worldline_dir(slug)
    if not wl_dir.is_dir():
        return f"ERROR: worldline '{slug}' not found."
    state = _read(wl_dir / "state.md")
    items = _read(wl_dir / "items.md")
    return f"{state}\n\n---\n\n{items}"


@tool()
def list_worldlines() -> str:
    """List all worldline slugs, one per line.
    Returns '(none)' if no worldlines exist yet."""
    if err := _check_initialized():
        return err
    if not WORLDLINES_DIR.exists():
        return "(none)"
    slugs = [
        d.name
        for d in sorted(WORLDLINES_DIR.iterdir())
        if d.is_dir() and d.name != ".gitkeep"
    ]
    return "\n".join(slugs) if slugs else "(none)"


@tool()
def read_archive(slug: str, period: str) -> str:
    """Read an archive file for a worldline.

    slug:   worldline name
    period: 'recent' for the last-7-days file, 'YYYY-MM' for a monthly file,
            or 'YYYY' for a yearly file
    """
    if err := _check_initialized():
        return err
    archive_dir = _worldline_dir(slug) / "archive"
    filename = "recent.md" if period == "recent" else f"{period}.md"
    return _read(archive_dir / filename)


@tool()
def read_divergence(slug: str) -> str:
    """Read a worldline divergence file.

    slug: divergence identifier without the 'div-' prefix
          (e.g. 'home-job-relocation' for div-home-job-relocation.md)
    """
    if err := _check_initialized():
        return err
    return _read(DIVERGENCES_DIR / f"div-{slug}.md")


@tool()
def list_divergences() -> str:
    """List all divergence slugs (without the 'div-' prefix), one per line.
    Returns '(none)' if no divergences exist."""
    if err := _check_initialized():
        return err
    if not DIVERGENCES_DIR.exists():
        return "(none)"
    slugs = [
        f.stem.removeprefix("div-")
        for f in sorted(DIVERGENCES_DIR.iterdir())
        if f.suffix == ".md"
    ]
    return "\n".join(slugs) if slugs else "(none)"


@tool()
def read_preferences(scope: str = "global") -> str:
    """Read a preferences YAML file.

    scope: 'global' for attractor/preferences.yaml,
           or a worldline slug for that worldline's preferences.yaml
    """
    if err := _check_initialized():
        return err
    if scope == "global":
        return _read(ATTRACTOR_DIR / "preferences.yaml")
    return _read(_worldline_dir(scope) / "preferences.yaml")


# ── Write tools ───────────────────────────────────────────────────────────────

@tool()
def write_ship_log(content: str) -> str:
    """Overwrite the Ship Log with new content.
    Always update last_updated timestamp in the content before calling."""
    if err := _check_initialized():
        return err
    return _write(ATTRACTOR_DIR / "ship-log.md", content)


@tool()
def write_worldline_state(slug: str, content: str) -> str:
    """Overwrite state.md for a worldline.
    Always update last_updated timestamp in the content before calling.

    slug: worldline directory name
    """
    if err := _check_initialized():
        return err
    if not _worldline_dir(slug).is_dir():
        return f"ERROR: worldline '{slug}' not found. Use create_worldline first."
    return _write(_worldline_dir(slug) / "state.md", content)


@tool()
def write_worldline_items(slug: str, content: str) -> str:
    """Overwrite items.md for a worldline.
    Always update last_updated timestamp in the content before calling.

    slug: worldline directory name
    """
    if err := _check_initialized():
        return err
    if not _worldline_dir(slug).is_dir():
        return f"ERROR: worldline '{slug}' not found. Use create_worldline first."
    return _write(_worldline_dir(slug) / "items.md", content)


@tool()
def create_worldline(slug: str) -> str:
    """Create a new worldline directory with template files.
    Fails if the worldline already exists.

    slug: lowercase hyphen-separated name (e.g. 'work-projectx')
          Must contain only lowercase letters, digits, and hyphens.
    """
    if err := _check_initialized():
        return err
    if not slug or not all(c.isalnum() or c == "-" for c in slug) or slug != slug.lower():
        return f"ERROR: invalid slug '{slug}'. Use lowercase letters, digits, and hyphens only."
    wl_dir = _worldline_dir(slug)
    if wl_dir.exists():
        return f"ERROR: worldline '{slug}' already exists."

    today = _today()
    results = [
        _write(wl_dir / "state.md",            _state_template(slug, today)),
        _write(wl_dir / "items.md",             _items_template(slug, today)),
        _write(wl_dir / "preferences.yaml",     _prefs_template()),
        _write(wl_dir / "archive" / "recent.md", _archive_recent_template(slug, today)),
    ]
    errors = [r for r in results if r.startswith("ERROR")]
    if errors:
        return "\n".join(errors)
    return f"ok: worldline '{slug}' created"


@tool()
def delete_worldline(slug: str) -> str:
    """Remove a worldline directory and all its contents.

    This is a destructive operation. The caller must generate an Imprint
    export for the worldline before calling this tool.

    slug: worldline directory name
    """
    if err := _check_initialized():
        return err
    wl_dir = _worldline_dir(slug)
    if not wl_dir.is_dir():
        return f"ERROR: worldline '{slug}' not found."
    import shutil
    try:
        shutil.rmtree(wl_dir)
        # Restore .gitkeep if worldlines/ is now empty
        remaining = [d for d in WORLDLINES_DIR.iterdir() if d.is_dir()]
        if not remaining:
            (WORLDLINES_DIR / ".gitkeep").touch()
        return f"ok: worldline '{slug}' deleted"
    except OSError as exc:
        return f"ERROR: {exc}"


@tool()
def write_divergence(slug: str, content: str) -> str:
    """Create or overwrite a worldline divergence file.

    slug: divergence identifier without the 'div-' prefix
          (e.g. 'home-job-relocation' writes to div-home-job-relocation.md)
    """
    if err := _check_initialized():
        return err
    return _write(DIVERGENCES_DIR / f"div-{slug}.md", content)


@tool()
def write_archive(slug: str, period: str, content: str) -> str:
    """Write an archive file for a worldline.

    slug:   worldline name
    period: 'recent' | 'YYYY-MM' | 'YYYY'
    """
    if err := _check_initialized():
        return err
    archive_dir = _worldline_dir(slug) / "archive"
    filename = "recent.md" if period == "recent" else f"{period}.md"
    return _write(archive_dir / filename, content)


@tool()
def read_okr_index() -> str:
    """Read the OKR index (attractor/okr.md).
    Returns the full content, or a not-found message if the file doesn't exist yet."""
    if err := _check_initialized():
        return err
    path = ATTRACTOR_DIR / "okr.md"
    if not path.exists():
        return "(OKR index not yet created. Use write_okr_index to initialise it.)"
    return _read(path)


@tool()
def write_okr_index(content: str) -> str:
    """Create or overwrite the OKR index (attractor/okr.md).
    Always update last_updated in the content before calling."""
    if err := _check_initialized():
        return err
    return _write(ATTRACTOR_DIR / "okr.md", content)


@tool()
def write_imprint(content: str) -> str:
    """Write an Imprint export to ~/hollow-backups/imprint-{today}.txt.

    Stored outside the ~/.hollow-attractor repo — never committed, never gitignored.
    Returns the full absolute path on success.
    """
    if err := _check_initialized():
        return err
    path = BACKUP_DIR / f"imprint-{_today()}.txt"
    result = _write(path, content)
    return f"ok: {path}" if result == "ok" else result


# Keep legacy alias so old Reading Steiner calls still work during migration
@tool()
def write_reading_steiner(content: str) -> str:
    """Deprecated alias for write_imprint. Use write_imprint instead."""
    return write_imprint(content)


# ── Git tools ─────────────────────────────────────────────────────────────────

@tool()
def commit(message: str) -> str:
    """Stage all changes in ~/.hollow-attractor and create a git commit.

    Git identity is always 'Hollow Attractor <hollow@local>' (set at bootstrap).
    Call this after every meaningful update per the Hollow Attractor protocol.

    message: full commit message following Hollow Attractor conventions,
             e.g. 'hollow: [work-projectx] add WAI-001 feature ramp blocked'
    """
    if err := _check_initialized():
        return err
    code, out = _git("add", ".")
    if code != 0:
        return f"ERROR (git add): {out}"
    code, out = _git("commit", "-m", message)
    if code != 0:
        if "nothing to commit" in out:
            return "ok: nothing to commit"
        return f"ERROR (git commit): {out}"
    return f"ok: {out}"


# ── Utility tools ─────────────────────────────────────────────────────────────

@tool()
def initialized() -> str:
    """Check whether ~/.hollow-attractor is a valid Hollow Attractor installation.
    Returns 'true' or 'false'."""
    return "true" if (ROOT_DIR / ".git").exists() else "false"


@tool()
def get_version() -> str:
    """Read hollow_version from global preferences.yaml."""
    prefs = ATTRACTOR_DIR / "preferences.yaml"
    if not prefs.exists():
        return "ERROR: preferences.yaml not found"
    for line in prefs.read_text(encoding="utf-8").splitlines():
        if line.startswith("hollow_version:"):
            return line.split(":", 1)[1].strip()
    # Fallback: support legacy kurisu_version key during migration
    for line in prefs.read_text(encoding="utf-8").splitlines():
        if line.startswith("kurisu_version:"):
            return line.split(":", 1)[1].strip()
    return "ERROR: hollow_version key not found in preferences.yaml"


# ── Prompts ───────────────────────────────────────────────────────────────────

@mcp.prompt()
def hollow_start() -> str:
    """Initialize a Hollow Attractor session.

    Loads the system prompt and the current Ship Log so Claude has full protocol
    context and current worldline state in a single invocation.
    Use this at the start of every Claude Desktop session.
    """
    # Load system prompt
    if not SYSTEM_PROMPT_PATH.exists():
        return (
            f"ERROR: SYSTEM_PROMPT.md not found at {SYSTEM_PROMPT_PATH}. "
            "Check that the Hollow Attractor repo is at its expected location."
        )
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    # Load current Ship Log if ~/.hollow-attractor is initialized
    session_state = ""
    if (ROOT_DIR / ".git").exists():
        ship_log_path = ATTRACTOR_DIR / "ship-log.md"
        if ship_log_path.exists():
            ship_log = ship_log_path.read_text(encoding="utf-8")
            session_state = f"\n\n---\n\n## Current Session State\n\n{ship_log}"
        else:
            session_state = "\n\n---\n\n## Current Session State\n\nShip Log not found."
    else:
        session_state = (
            "\n\n---\n\n## Current Session State\n\n"
            "~/.hollow-attractor is not initialized. "
            "Run hollow-init.sh to bootstrap, then start a new session."
        )

    return (
        f"{system_prompt}"
        f"{session_state}"
        f"\n\n---\n\n"
        f"You are now operating as Hollow Attractor. "
        f"Acknowledge your active worldlines and any due reminders, "
        f"then wait for the user's first invocation."
    )


# ── Schema cleanup ────────────────────────────────────────────────────────────
# Strip pydantic-generated "title" from the top-level inputSchema object on
# every tool. Pydantic emits e.g. {"title": "read_ship_logArguments", ...}.
# The "title" key is not part of the MCP 2024-11-05 inputSchema spec and
# may cause Claude Code to silently reject the entire tools/list response.
for _t in mcp._tool_manager._tools.values():
    _t.parameters.pop("title", None)


# ── Smoke test ────────────────────────────────────────────────────────────────

def _smoke_test() -> None:
    """Run basic read operations against ~/.hollow-attractor and report results."""
    print("Hollow Attractor MCP Server — smoke test")
    print(f"  ROOT_DIR: {ROOT_DIR}")
    print()

    checks = [
        ("initialized",      initialized()),
        ("get_version",      get_version()),
        ("list_worldlines",  list_worldlines()),
        ("list_divergences", list_divergences()),
        ("read_ship_log",    read_ship_log()[:80] + "..."),
        ("hollow_start",     "OK" if not hollow_start().startswith("ERROR") else hollow_start()),
        ("SYSTEM_PROMPT.md", f"found at {SYSTEM_PROMPT_PATH}" if SYSTEM_PROMPT_PATH.exists() else f"MISSING: {SYSTEM_PROMPT_PATH}"),
    ]
    for name, result in checks:
        status = "FAIL" if result.startswith("ERROR") else "OK"
        print(f"  [{status}] {name}")
        if status == "FAIL":
            print(f"         {result}")
    print()
    print("Done.")


# ── Entry point ───────────────────────────────────────────────────────────────
#
# Usage:
#   python3 server.py               stdio mode (for local Claude Desktop config)
#   python3 server.py --test        smoke test against ~/.hollow-attractor

if __name__ == "__main__":
    args = sys.argv[1:]

    if args and args[0] == "--test":
        _smoke_test()

    else:
        # Default: stdio transport for local process invocation
        mcp.run()
