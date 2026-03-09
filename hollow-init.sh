#!/usr/bin/env bash
# kurisu-init.sh
# Bootstraps a new ~/.kurisu installation.
# Safe to inspect before running. Creates no files outside ~/.kurisu.

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

KURISU_DIR="${KURISU_DIR:-$HOME/.kurisu}"
KURISU_VERSION="0.1.0"
TODAY="$(date +%Y-%m-%d)"

# ── Helpers ───────────────────────────────────────────────────────────────────

info()    { printf '\033[0;34m[kurisu]\033[0m %s\n' "$*"; }
success() { printf '\033[0;32m[kurisu]\033[0m %s\n' "$*"; }
warn()    { printf '\033[0;33m[kurisu]\033[0m %s\n' "$*" >&2; }
die()     { printf '\033[0;31m[kurisu]\033[0m %s\n' "$*" >&2; exit 1; }

# ── Preflight ─────────────────────────────────────────────────────────────────

command -v git >/dev/null 2>&1 || die "git is required but not found in PATH."

if [[ -d "$KURISU_DIR/.git" ]]; then
    die "~/.kurisu is already initialized. To re-initialize, remove $KURISU_DIR first."
fi

if [[ -e "$KURISU_DIR" && ! -d "$KURISU_DIR" ]]; then
    die "$KURISU_DIR exists and is not a directory."
fi

# ── Directory structure ───────────────────────────────────────────────────────

info "Creating directory structure at $KURISU_DIR"

mkdir -p \
    "$KURISU_DIR/attractor/divergences" \
    "$KURISU_DIR/worldlines"

# ── .gitignore ────────────────────────────────────────────────────────────────

cat > "$KURISU_DIR/.gitignore" << 'EOF'
# Reading Steiner exports are portable artifacts, not managed state.
reading-steiner-*.txt
EOF

# ── attractor/preferences.yaml ────────────────────────────────────────────────

cat > "$KURISU_DIR/attractor/preferences.yaml" << EOF
kurisu_version: $KURISU_VERSION
reminder_surfacing: on_invocation   # on_invocation | disabled
dmail_threshold_days: 7
stale_question_days: 14
git_auto_commit: true
default_worldline: null             # null = attractor state on session start
EOF

# ── attractor/ship-log.md ─────────────────────────────────────────────────────

cat > "$KURISU_DIR/attractor/ship-log.md" << EOF
# Ship Log
last_updated: $TODAY

## Active Worldlines
(none)

## Active Divergences
(none)

## Resolved Divergences
(none)

## Recent Meaningful Updates (rolling 14 days)
- $TODAY: [attractor] kurisu bootstrapped — version $KURISU_VERSION

## Reminders
(none)

## D-Mail History
(none)
EOF

# ── attractor/divergences/.gitkeep ───────────────────────────────────────────
# Git does not track empty directories. This placeholder is removed automatically
# when the first real divergence file is created.

touch "$KURISU_DIR/attractor/divergences/.gitkeep"

# ── worldlines/.gitkeep ───────────────────────────────────────────────────────
# Same pattern. Removed when the first worldline is created.

touch "$KURISU_DIR/worldlines/.gitkeep"

# ── Git init ─────────────────────────────────────────────────────────────────

info "Initializing git repository"

git -C "$KURISU_DIR" init --quiet

# Identity is set locally so it never conflicts with the user's global git config.
git -C "$KURISU_DIR" config --local user.email "kurisu@local"
git -C "$KURISU_DIR" config --local user.name  "Kurisu"

# ── Initial commit ────────────────────────────────────────────────────────────

git -C "$KURISU_DIR" add .
git -C "$KURISU_DIR" commit --quiet -m "kurisu: bootstrap"

# ── Done ──────────────────────────────────────────────────────────────────────

success "Bootstrap complete."
echo
echo "  Location : $KURISU_DIR"
echo "  Version  : $KURISU_VERSION"
echo "  Git log  :"
git -C "$KURISU_DIR" log --oneline
echo
echo "  ~/.kurisu contains sensitive personal data."
echo "  Do not push to a public remote."
echo
info "Start a Kurisu session and say: kurisu, create a new worldline"
