#!/usr/bin/env python3
"""hollow — Hollow Attractor CLI

Commands:
  hollow init               Bootstrap ~/.hollow-attractor
  hollow serve              Run MCP server over HTTP on localhost (default port 7412)
  hollow serve --port N     Run on a custom port
  hollow serve --daemon     Run in background, logs to /tmp/hollow-serve.log
  hollow serve --stop       Stop a running daemon
  hollow serve --status     Check if daemon is running
  hollow                    Run MCP server via stdio (used by Claude Desktop)
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
    elif args and args[0] == "rename-worldline":
        if len(args) != 3:
            print("Usage: hollow rename-worldline <old-slug> <new-slug>", file=sys.stderr)
            sys.exit(1)
        _rename_worldline(args[1], args[2])
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
        print("  hollow init                          Bootstrap ~/.hollow-attractor")
        print("  hollow rename-worldline <old> <new>  Rename a worldline slug atomically")
        print("  hollow serve                         Run MCP server over HTTP on localhost:7412")
        print("  hollow serve --port N                Run HTTP server on a custom port")
        print("  hollow serve --daemon                Run HTTP server in background")
        print("  hollow serve --stop                  Stop the background server")
        print("  hollow serve --status                Check if background server is running")
        print("  hollow --version                     Show version")
        print("  hollow                    Run MCP server via stdio (used by Claude Desktop)")
        print()
        print("See https://github.com/wjdhollow/hollow-attractor for setup instructions.")
        if args:
            print(f"\nUnknown command: {args[0]}", file=sys.stderr)
            sys.exit(1)


_PID_FILE = Path("/tmp/hollow-serve.pid")
_LOG_FILE = Path("/tmp/hollow-serve.log")


def _serve(args: list[str]) -> None:
    port = 7412
    daemon = False
    stop = False
    status = False

    i = 0
    while i < len(args):
        if args[i] in ("--port", "-p") and i + 1 < len(args):
            try:
                port = int(args[i + 1])
            except ValueError:
                print(f"Invalid port: {args[i + 1]}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--daemon":
            daemon = True
            i += 1
        elif args[i] == "--stop":
            stop = True
            i += 1
        elif args[i] == "--status":
            status = True
            i += 1
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    if stop:
        _serve_stop()
        return

    if status:
        _serve_status()
        return

    if daemon:
        _serve_daemon(port)
        return

    # Foreground mode
    from mcp_server.server import mcp
    mcp.settings.port = port
    mcp.settings.host = "127.0.0.1"
    print(f"Hollow Attractor MCP server listening on http://127.0.0.1:{port}/mcp")
    print("Add to Claude Code ~/.claude.json:")
    print(f'  "hollow-attractor": {{"type": "http", "url": "http://127.0.0.1:{port}/mcp"}}')
    print("Press Ctrl+C to stop.")
    mcp.run(transport="streamable-http")


def _serve_daemon(port: int) -> None:
    import os
    import time

    if _PID_FILE.exists():
        pid = int(_PID_FILE.read_text().strip())
        try:
            os.kill(pid, 0)
            print(f"Already running (PID {pid}). Use: hollow serve --stop")
            sys.exit(1)
        except OSError:
            _PID_FILE.unlink()  # stale PID file

    # Fork to background
    pid = os.fork()
    if pid > 0:
        # Parent: wait briefly then confirm child started
        time.sleep(1)
        if _PID_FILE.exists() and int(_PID_FILE.read_text().strip()) == pid:
            print(f"Hollow Attractor MCP server started (PID {pid})")
            print(f"URL:  http://127.0.0.1:{port}/mcp")
            print(f"Logs: {_LOG_FILE}")
            print("Stop: hollow serve --stop")
        else:
            print(f"Server may have failed to start. Check {_LOG_FILE}", file=sys.stderr)
        return

    # Child: detach from terminal and run server
    os.setsid()
    with open(_LOG_FILE, "a") as log:
        sys.stdout = log
        sys.stderr = log
        _PID_FILE.write_text(str(os.getpid()))
        try:
            from mcp_server.server import mcp
            mcp.settings.port = port
            mcp.settings.host = "127.0.0.1"
            mcp.run(transport="streamable-http")
        finally:
            if _PID_FILE.exists():
                _PID_FILE.unlink()


def _serve_stop() -> None:
    import os

    if not _PID_FILE.exists():
        print("No running daemon found.")
        return

    pid = int(_PID_FILE.read_text().strip())
    try:
        os.kill(pid, 15)  # SIGTERM
        _PID_FILE.unlink()
        print(f"Stopped (PID {pid}).")
    except OSError:
        print(f"Process {pid} not found — removing stale PID file.")
        _PID_FILE.unlink()


def _serve_status() -> None:
    import os

    if not _PID_FILE.exists():
        print("hollow serve: not running")
        return

    pid = int(_PID_FILE.read_text().strip())
    try:
        os.kill(pid, 0)
        print(f"hollow serve: running (PID {pid})")
    except OSError:
        print("hollow serve: not running (stale PID file)")
        _PID_FILE.unlink()


def _rename_worldline(old: str, new: str) -> None:
    import os
    import re
    import shutil

    hollow_dir = Path(os.environ.get("HOLLOW_DIR", str(Path.home() / ".hollow-attractor")))

    def die(msg: str) -> None:
        print(f"\033[0;31m[hollow]\033[0m {msg}", file=sys.stderr)
        sys.exit(1)

    def info(msg: str) -> None:
        print(f"\033[0;34m[hollow]\033[0m {msg}")

    def success(msg: str) -> None:
        print(f"\033[0;32m[hollow]\033[0m {msg}")

    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(hollow_dir), *args], check=True, capture_output=True)

    # Validate slugs
    def valid_slug(s: str) -> bool:
        return bool(s) and all(c.isalnum() or c == "-" for c in s) and s == s.lower()

    if not valid_slug(old):
        die(f"Invalid slug '{old}'. Use lowercase letters, digits, and hyphens only.")
    if not valid_slug(new):
        die(f"Invalid slug '{new}'. Use lowercase letters, digits, and hyphens only.")
    if old == new:
        die("Old and new slugs are the same.")

    old_dir = hollow_dir / "worldlines" / old
    new_dir = hollow_dir / "worldlines" / new

    if not old_dir.is_dir():
        die(f"Worldline '{old}' not found.")
    if new_dir.exists():
        die(f"Worldline '{new}' already exists.")

    info(f"Renaming worldline '{old}' → '{new}'")

    # Copy directory
    shutil.copytree(old_dir, new_dir)

    # Update slug references in state.md and items.md headers
    for filename, pattern, replacement in [
        ("state.md",  f"# Worldline: {old}", f"# Worldline: {new}"),
        ("items.md",  f"# Items: {old}",     f"# Items: {new}"),
    ]:
        path = new_dir / filename
        if path.exists():
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace(pattern, replacement, 1), encoding="utf-8")

    # Update archive headers
    archive_dir = new_dir / "archive"
    if archive_dir.is_dir():
        for md in archive_dir.glob("*.md"):
            text = md.read_text(encoding="utf-8")
            updated = re.sub(rf"\b{re.escape(old)}\b", new, text)
            if updated != text:
                md.write_text(updated, encoding="utf-8")

    # Update Ship Log — replace old slug entry with new slug
    ship_log = hollow_dir / "attractor" / "ship-log.md"
    if ship_log.exists():
        text = ship_log.read_text(encoding="utf-8")
        updated = re.sub(rf"\b{re.escape(old)}\b", new, text)
        if updated != text:
            ship_log.write_text(updated, encoding="utf-8")
            info("Ship Log updated.")

    # Delete old directory
    shutil.rmtree(old_dir)

    # Commit
    git("add", ".")
    git("commit", "-m", f"hollow: rename worldline {old} → {new}")

    success(f"Worldline '{old}' renamed to '{new}'.")
    print()
    print(f"  Note: if '{old}' is referenced in divergence files or other worldlines'")
    print(f"  state.md, update those references manually or via a Hollow Attractor session.")


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
