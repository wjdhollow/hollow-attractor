#!/usr/bin/env bash
# scripts/setup-mcp.sh
# Installs the Hollow Attractor MCP server dependencies and verifies the setup.
# Run once after cloning the repo.
#
# Prefers uv (https://docs.astral.sh/uv/) as the package manager.
# Falls back to pip if uv is not available.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER="$REPO_DIR/mcp_server/server.py"

info()    { printf '\033[0;34m[hollow-attractor]\033[0m %s\n' "$*"; }
success() { printf '\033[0;32m[hollow-attractor]\033[0m %s\n' "$*"; }
warn()    { printf '\033[0;33m[hollow-attractor]\033[0m %s\n' "$*"; }
die()     { printf '\033[0;31m[hollow-attractor]\033[0m %s\n' "$*" >&2; exit 1; }

# ── Check Python ──────────────────────────────────────────────────────────────

command -v python3 >/dev/null 2>&1 || die "python3 not found. Install Python 3.10 or later."

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 10 ]]; then
    die "Python 3.10+ required. Found: $PY_VERSION"
fi

info "Python $PY_VERSION found"

# ── Detect package manager (prefer uv) ───────────────────────────────────────

USE_UV=false
PYTHON_CMD="python3"

if command -v uv >/dev/null 2>&1; then
    info "uv found — using uv for dependency management"
    USE_UV=true
elif command -v pip3 >/dev/null 2>&1; then
    info "pip3 found — using pip3 for dependency management"
    PYTHON_CMD="python3"
elif command -v pip >/dev/null 2>&1; then
    info "pip found — using pip for dependency management"
    PYTHON_CMD="python3"
else
    warn "Neither uv nor pip found."
    echo
    echo "  Recommended: install uv (fast, no pip required)"
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "    source \$HOME/.local/bin/env  # or restart your shell"
    echo
    echo "  Alternative: install pip via apt"
    echo "    sudo apt install python3-pip"
    echo
    die "Install uv or pip, then re-run this script."
fi

# ── Install dependencies ──────────────────────────────────────────────────────

if [[ "$USE_UV" == "true" ]]; then
    info "Installing dependencies with uv"
    uv sync --project "$REPO_DIR" --quiet
    PYTHON_CMD="uv run --project $REPO_DIR python3"
else
    info "Installing dependencies with pip"
    pip3 install -q -r "$REPO_DIR/requirements.txt"
fi

success "Dependencies installed"

# ── Smoke test ────────────────────────────────────────────────────────────────

info "Running smoke test against ~/.hollow-attractor"
$PYTHON_CMD "$SERVER" --test

# ── Print Claude Desktop config ───────────────────────────────────────────────

echo
success "MCP server is ready."
echo
echo "──────────────────────────────────────────────────────────────────────────"
echo "  Claude Desktop configuration"
echo "  File: %APPDATA%\\Claude\\claude_desktop_config.json  (Windows)"
echo "  WSL:  /mnt/c/Users/\$(cmd.exe /c 'echo %USERNAME%' 2>/dev/null | tr -d '\\r')/AppData/Roaming/Claude/claude_desktop_config.json"
echo "──────────────────────────────────────────────────────────────────────────"
echo

if [[ "$USE_UV" == "true" ]]; then
    UV_PATH="$(command -v uv)"
    cat << EOF
{
  "mcpServers": {
    "hollow-attractor": {
      "command": "wsl",
      "args": [
        "-e",
        "$UV_PATH",
        "run",
        "--project",
        "$REPO_DIR",
        "python3",
        "$SERVER"
      ]
    }
  }
}
EOF
else
    PYTHON_PATH="$(command -v python3)"
    cat << EOF
{
  "mcpServers": {
    "hollow-attractor": {
      "command": "wsl",
      "args": [
        "-e",
        "$PYTHON_PATH",
        "$SERVER"
      ]
    }
  }
}
EOF
fi

echo
echo "  If claude_desktop_config.json already has other mcpServers entries,"
echo "  merge the 'hollow-attractor' block into the existing 'mcpServers' object."
echo
info "Restart Claude Desktop after saving the config."
