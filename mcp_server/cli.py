#!/usr/bin/env python3
"""hollow — Hollow Attractor CLI

Commands:
  hollow init             Bootstrap ~/.hollow-attractor
  hollow serve            Run MCP server over HTTP on localhost (default port 7412)
  hollow serve --port N   Run on a custom port
  hollow                  Run MCP server via stdio (used by Claude Desktop)
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path


def main() -> None:
    args = sys.argv[1:]

    if args and args[0] == "init":
        _init()
    elif args and args[0] == "serve":
        _serve(args[1:])
    elif args and args[0] in ("--version", "-V"):
        from importlib.metadata import version
        print(version("hollow-attractor"))
    elif not args and not sys.stdin.isatty():
        # Stdin is a pipe with no args: MCP stdio transport for Claude Desktop
        from mcp_server.server import mcp
        mcp.run()
    else:
        # Interactive terminal (with or without unrecognized args) — show help
        print("Hollow Attractor")
        print()
        print("Usage:")
        print("  hollow init             Bootstrap ~/.hollow-attractor")
        print("  hollow serve            Run MCP server over HTTP on localhost:7412")
        print("  hollow serve --port N   Run HTTP server on a custom port")
        print("  hollow --version        Show version")
        print("  hollow                  Run MCP server via stdio (used by Claude Desktop)")
        print()
        print("See https://github.com/wjdhollow/hollow-attractor for setup instructions.")
        if args:
            print(f"\nUnknown command: {args[0]}", file=sys.stderr)
            sys.exit(1)


def _serve(args: list[str]) -> None:
    port = 7412
    i = 0
    while i < len(args):
        if args[i] in ("--port", "-p") and i + 1 < len(args):
            try:
                port = int(args[i + 1])
            except ValueError:
                print(f"Invalid port: {args[i + 1]}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    from mcp_server.server import mcp
    mcp.settings.port = port
    mcp.settings.host = "127.0.0.1"
    print(f"Hollow Attractor MCP server listening on http://127.0.0.1:{port}/mcp")
    print("Add to Claude Code ~/.claude.json:")
    print(f'  "hollow-attractor": {{"type": "http", "url": "http://127.0.0.1:{port}/mcp"}}')
    print("Press Ctrl+C to stop.")
    mcp.run(transport="streamable-http")


def _init() -> None:
    import os

    hollow_dir = Path(os.environ.get("HOLLOW_DIR", str(Path.home() / ".hollow-attractor")))
    hollow_version = "0.2.0"
    today = date.today().isoformat()

    def info(msg: str) -> None:
        print(f"\033[0;34m[hollow]\033[0m {msg}")

    def success(msg: str) -> None:
        print(f"\033[0;32m[hollow]\033[0m {msg}")

    def die(msg: str) -> None:
        print(f"\033[0;31m[hollow]\033[0m {msg}", file=sys.stderr)
        sys.exit(1)

    # Preflight
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        die("git is required but not found in PATH.")

    if (hollow_dir / ".git").exists():
        die(f"{hollow_dir} is already initialized. To re-initialize, remove {hollow_dir} first.")

    if hollow_dir.exists() and not hollow_dir.is_dir():
        die(f"{hollow_dir} exists and is not a directory.")

    # Directory structure
    info(f"Creating directory structure at {hollow_dir}")
    for subdir in ["attractor/divergences", "worldlines"]:
        (hollow_dir / subdir).mkdir(parents=True, exist_ok=True)

    # .gitignore
    (hollow_dir / ".gitignore").write_text(
        "# Imprint exports are portable artifacts, not managed state.\n"
        "imprint-*.txt\n"
    )

    # attractor/preferences.yaml
    (hollow_dir / "attractor" / "preferences.yaml").write_text(
        f"hollow_version: {hollow_version}\n"
        "reminder_surfacing: on_invocation   # on_invocation | disabled\n"
        "anneal_threshold_days: 7\n"
        "stale_question_days: 14\n"
        "git_auto_commit: true\n"
        "default_worldline: null             # null = attractor state on session start\n"
    )

    # attractor/ship-log.md
    (hollow_dir / "attractor" / "ship-log.md").write_text(
        "# Ship Log\n"
        f"last_updated: {today}\n\n"
        "## Active Worldlines\n(none)\n\n"
        "## Active Divergences\n(none)\n\n"
        "## Resolved Divergences\n(none)\n\n"
        "## Recent Meaningful Updates (rolling 14 days)\n"
        f"- {today}: [attractor] hollow-attractor bootstrapped — version {hollow_version}\n\n"
        "## Reminders\n(none)\n\n"
        "## Anneal History\n(none)\n"
    )

    # .gitkeep placeholders (removed when first real files are created)
    (hollow_dir / "attractor" / "divergences" / ".gitkeep").touch()
    (hollow_dir / "worldlines" / ".gitkeep").touch()

    # Git init
    info("Initializing git repository")

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(hollow_dir), *args], check=True, capture_output=True)

    git("init", "--quiet")
    git("config", "--local", "user.email", "hollow@local")
    git("config", "--local", "user.name", "Hollow Attractor")
    git("add", ".")
    git("commit", "--quiet", "-m", "hollow: bootstrap")

    success("Bootstrap complete.")
    print()
    print(f"  Location : {hollow_dir}")
    print(f"  Version  : {hollow_version}")
    print( "  Git log  :")
    subprocess.run(["git", "-C", str(hollow_dir), "log", "--oneline"])
    print()
    print(f"  {hollow_dir} contains sensitive personal data.")
    print( "  Do not push to a public remote.")
    print()
    info("Next: add hollow-attractor to your Claude Desktop MCP config.")
    info("See: https://github.com/wjdhollow/hollow-attractor#install")
