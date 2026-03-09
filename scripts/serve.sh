#!/usr/bin/env bash
# scripts/serve.sh
# Start the Kurisu MCP server in HTTP mode.
# Claude Desktop connects to http://localhost:8765/mcp
#
# Usage:
#   bash scripts/serve.sh           # foreground (Ctrl+C to stop)
#   bash scripts/serve.sh --daemon  # background, logs to /tmp/kurisu-mcp.log

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER="$REPO_DIR/mcp_server/server.py"
PORT="${KURISU_PORT:-8765}"
LOG="/tmp/kurisu-mcp.log"
UV="${UV:-$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")}"

info() { printf '\033[0;34m[kurisu]\033[0m %s\n' "$*"; }
die()  { printf '\033[0;31m[kurisu]\033[0m %s\n' "$*" >&2; exit 1; }

[[ -f "$SERVER" ]] || die "server.py not found at $SERVER"
command -v "$UV" >/dev/null 2>&1 || die "uv not found at $UV. Run scripts/setup-mcp.sh first."

if [[ "${1:-}" == "--daemon" ]]; then
    info "Starting Kurisu MCP server in background on port $PORT"
    info "Logs: $LOG"
    nohup "$UV" run --project "$REPO_DIR" python3 "$SERVER" --serve "$PORT" \
        > "$LOG" 2>&1 &
    echo $! > /tmp/kurisu-mcp.pid
    sleep 1
    if kill -0 "$(cat /tmp/kurisu-mcp.pid)" 2>/dev/null; then
        info "Server started (PID $(cat /tmp/kurisu-mcp.pid))"
        info "Connect Claude Desktop to: http://localhost:$PORT/mcp"
        info "Stop with: bash scripts/serve.sh --stop"
    else
        die "Server failed to start. Check $LOG"
    fi

elif [[ "${1:-}" == "--stop" ]]; then
    if [[ -f /tmp/kurisu-mcp.pid ]]; then
        PID=$(cat /tmp/kurisu-mcp.pid)
        kill "$PID" 2>/dev/null && info "Stopped server (PID $PID)" || info "Server was not running"
        rm -f /tmp/kurisu-mcp.pid
    else
        info "No PID file found — server may not be running"
    fi

elif [[ "${1:-}" == "--status" ]]; then
    if [[ -f /tmp/kurisu-mcp.pid ]] && kill -0 "$(cat /tmp/kurisu-mcp.pid)" 2>/dev/null; then
        info "Server is running (PID $(cat /tmp/kurisu-mcp.pid)) on port $PORT"
    else
        info "Server is not running"
    fi

else
    # Foreground mode — useful for watching logs during integration testing
    info "Starting Kurisu MCP server (foreground) on port $PORT"
    info "Connect Claude Desktop to: http://localhost:$PORT/mcp"
    info "Press Ctrl+C to stop"
    exec "$UV" run --project "$REPO_DIR" python3 "$SERVER" --serve "$PORT"
fi
