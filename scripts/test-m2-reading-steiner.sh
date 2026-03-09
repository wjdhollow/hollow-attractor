#!/usr/bin/env bash
# scripts/test-m2-reading-steiner.sh
# M2: Reading Steiner end-to-end test.
#
# Tests that a Reading Steiner generated from the real ~/.kurisu can be used
# to re-bootstrap a fresh installation without data loss.
#
# Does NOT touch ~/.kurisu. All re-bootstrap testing happens in /tmp/kurisu-rs-test.
#
# Usage:
#   bash scripts/test-m2-reading-steiner.sh <path-to-reading-steiner.txt>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER="$REPO_DIR/mcp_server/server.py"
UV="${UV:-$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")}"
TEST_DIR="/tmp/kurisu-rs-test"
RS_FILE="${1:-}"

info()    { printf '\033[0;34m[m2]\033[0m %s\n' "$*"; }
success() { printf '\033[0;32m[m2]\033[0m %s\n' "$*"; }
fail()    { printf '\033[0;31m[m2]\033[0m FAIL: %s\n' "$*"; FAILURES=$((FAILURES+1)); }
FAILURES=0

# ── Preflight ─────────────────────────────────────────────────────────────────

[[ -n "$RS_FILE" ]] || { echo "Usage: $0 <path-to-reading-steiner.txt>"; exit 1; }
[[ -f "$RS_FILE" ]] || { echo "File not found: $RS_FILE"; exit 1; }

info "Reading Steiner: $RS_FILE"
info "Test directory:  $TEST_DIR"
echo

# ── Phase 1: Inspect the Reading Steiner ─────────────────────────────────────

info "Phase 1 — Inspecting Reading Steiner format"

RS_CONTENT=$(cat "$RS_FILE")

check_contains() {
    local label="$1"
    local pattern="$2"
    if echo "$RS_CONTENT" | grep -q "$pattern"; then
        success "  $label"
    else
        fail "  $label (pattern not found: '$pattern')"
    fi
}

check_contains "Header present"              "KURISU — READING STEINER"
check_contains "Source version present"      "Source version:"
check_contains "At least one WORLDLINE block" "^WORLDLINE:"
check_contains "END marker present"          "END OF READING STEINER"
check_contains "Open items section"          "Open items:"
check_contains "Key decisions section"       "Key decisions:"
check_contains "References section"          "References:"

# Count worldlines in the file
WL_COUNT=$(echo "$RS_CONTENT" | grep -c "^WORLDLINE:" || true)
info "  Worldlines found in Reading Steiner: $WL_COUNT"
[[ "$WL_COUNT" -gt 0 ]] || fail "No worldlines found in Reading Steiner"

# Count worldlines in real ~/.kurisu for comparison
REAL_WL_COUNT=$(ls ~/.kurisu/worldlines/ | grep -v ".gitkeep" | wc -l)
info "  Worldlines in ~/.kurisu: $REAL_WL_COUNT"

if [[ "$WL_COUNT" -eq "$REAL_WL_COUNT" ]]; then
    success "  Worldline count matches"
else
    fail "  Worldline count mismatch: Reading Steiner has $WL_COUNT, ~/.kurisu has $REAL_WL_COUNT"
fi

echo

# ── Phase 2: Bootstrap a fresh test directory ─────────────────────────────────

info "Phase 2 — Bootstrapping fresh test directory"

# Clean up any previous test run
rm -rf "$TEST_DIR"

KURISU_DIR="$TEST_DIR" bash "$REPO_DIR/kurisu-init.sh" > /tmp/kurisu-rs-init.log 2>&1 \
    && success "  kurisu-init.sh completed" \
    || { fail "  kurisu-init.sh failed"; cat /tmp/kurisu-rs-init.log; exit 1; }

# Verify structure
for path in ".git" "attractor/ship-log.md" "attractor/preferences.yaml" "worldlines"; do
    if [[ -e "$TEST_DIR/$path" ]]; then
        success "  $path exists"
    else
        fail "  $path missing"
    fi
done

echo

# ── Phase 3: Simulate re-bootstrap by reading the Reading Steiner ─────────────

info "Phase 3 — Simulating re-bootstrap via MCP tools"

# Use the MCP server pointed at the test directory to verify read tools work
KURISU_DIR="$TEST_DIR" "$UV" run --project "$REPO_DIR" python3 "$SERVER" --test \
    > /tmp/kurisu-rs-server-test.log 2>&1 \
    && success "  MCP server smoke test passed against test directory" \
    || { fail "  MCP server smoke test failed"; cat /tmp/kurisu-rs-server-test.log; }

# Copy the Reading Steiner into the test directory (gitignored, as per spec)
cp "$RS_FILE" "$TEST_DIR/$(basename "$RS_FILE")"
success "  Reading Steiner copied to test directory"

# Verify it is gitignored
cd "$TEST_DIR"
if git -C "$TEST_DIR" status --porcelain | grep -q "reading-steiner"; then
    fail "  Reading Steiner is NOT gitignored — it appears in git status"
else
    success "  Reading Steiner is correctly gitignored"
fi
cd - > /dev/null

echo

# ── Phase 4: Verify the test directory is clean for re-bootstrap ─────────────

info "Phase 4 — Verifying test directory is re-bootstrap-ready"

# Check git log — should have exactly one commit (bootstrap)
COMMIT_COUNT=$(git -C "$TEST_DIR" log --oneline | wc -l)
if [[ "$COMMIT_COUNT" -eq 1 ]]; then
    success "  Git log: 1 commit (bootstrap only)"
else
    fail "  Git log: expected 1 commit, found $COMMIT_COUNT"
fi

GIT_AUTHOR=$(git -C "$TEST_DIR" log --format="%ae" -1)
if [[ "$GIT_AUTHOR" == "kurisu@local" ]]; then
    success "  Git author: kurisu@local"
else
    fail "  Git author: expected kurisu@local, got $GIT_AUTHOR"
fi

echo

# ── Summary ───────────────────────────────────────────────────────────────────

if [[ "$FAILURES" -eq 0 ]]; then
    success "M2 test passed. ($WL_COUNT worldlines verified, fresh bootstrap clean)"
    echo
    info "Test directory preserved at $TEST_DIR for manual inspection."
    info "Reading Steiner is ready for re-bootstrap. To complete M2:"
    info "  In Claude Desktop, run: kurisu, bootstrap from reading steiner $RS_FILE"
    info "  Then switch to the test directory and verify worldlines were reconstructed."
else
    echo
    printf '\033[0;31m[m2]\033[0m %d check(s) failed.\n' "$FAILURES"
    exit 1
fi
