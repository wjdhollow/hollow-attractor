#!/usr/bin/env bash
# hollow-init.sh
# Bootstraps a new ~/.hollow-attractor installation.
# Safe to inspect before running. Creates no files outside ~/.hollow-attractor.

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

HOLLOW_DIR="${HOLLOW_DIR:-$HOME/.hollow-attractor}"
HOLLOW_VERSION="0.2.0"
TODAY="$(date +%Y-%m-%d)"

# ── Helpers ───────────────────────────────────────────────────────────────────

info()    { printf '\033[0;34m[hollow]\033[0m %s\n' "$*"; }
success() { printf '\033[0;32m[hollow]\033[0m %s\n' "$*"; }
warn()    { printf '\033[0;33m[hollow]\033[0m %s\n' "$*" >&2; }
die()     { printf '\033[0;31m[hollow]\033[0m %s\n' "$*" >&2; exit 1; }

# ── Preflight ─────────────────────────────────────────────────────────────────

command -v git >/dev/null 2>&1 || die "git is required but not found in PATH."

if [[ -d "$HOLLOW_DIR/.git" ]]; then
    die "~/.hollow-attractor is already initialized. To re-initialize, remove $HOLLOW_DIR first."
fi

if [[ -e "$HOLLOW_DIR" && ! -d "$HOLLOW_DIR" ]]; then
    die "$HOLLOW_DIR exists and is not a directory."
fi

# ── Directory structure ───────────────────────────────────────────────────────

info "Creating directory structure at $HOLLOW_DIR"

mkdir -p \
    "$HOLLOW_DIR/attractor/divergences" \
    "$HOLLOW_DIR/worldlines"

# ── .gitignore ────────────────────────────────────────────────────────────────

cat > "$HOLLOW_DIR/.gitignore" << 'EOF'
# Imprint exports are portable artifacts, not managed state.
imprint-*.txt
EOF

# ── attractor/preferences.yaml ────────────────────────────────────────────────

cat > "$HOLLOW_DIR/attractor/preferences.yaml" << EOF
hollow_version: $HOLLOW_VERSION
reminder_surfacing: on_invocation   # on_invocation | disabled
anneal_threshold_days: 7
stale_question_days: 14
git_auto_commit: true
default_worldline: null             # null = attractor state on session start
EOF

# ── attractor/ship-log.md ─────────────────────────────────────────────────────

cat > "$HOLLOW_DIR/attractor/ship-log.md" << EOF
# Ship Log
last_updated: $TODAY

## Active Worldlines
(none)

## Active Divergences
(none)

## Resolved Divergences
(none)

## Recent Meaningful Updates (rolling 14 days)
- $TODAY: [attractor] hollow-attractor bootstrapped — version $HOLLOW_VERSION

## Reminders
(none)

## Anneal History
(none)
EOF

# ── attractor/divergences/.gitkeep ───────────────────────────────────────────
# Git does not track empty directories. This placeholder is removed automatically
# when the first real divergence file is created.

touch "$HOLLOW_DIR/attractor/divergences/.gitkeep"

# ── worldlines/.gitkeep ───────────────────────────────────────────────────────
# Same pattern. Removed when the first worldline is created.

touch "$HOLLOW_DIR/worldlines/.gitkeep"

# ── Git init ─────────────────────────────────────────────────────────────────

info "Initializing git repository"

git -C "$HOLLOW_DIR" init --quiet

# Identity is set locally so it never conflicts with the user's global git config.
git -C "$HOLLOW_DIR" config --local user.email "hollow@local"
git -C "$HOLLOW_DIR" config --local user.name  "Hollow Attractor"

# ── Initial commit ────────────────────────────────────────────────────────────

git -C "$HOLLOW_DIR" add .
git -C "$HOLLOW_DIR" commit --quiet -m "hollow: bootstrap"

# ── Done ──────────────────────────────────────────────────────────────────────

success "Bootstrap complete."
echo
echo "  Location : $HOLLOW_DIR"
echo "  Version  : $HOLLOW_VERSION"
echo "  Git log  :"
git -C "$HOLLOW_DIR" log --oneline
echo
echo "  ~/.hollow-attractor contains sensitive personal data."
echo "  Do not push to a public remote."
echo
info "Start a Hollow Attractor session and say: hollow, create a new worldline"
