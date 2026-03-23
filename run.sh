#!/bin/bash
# Daily AI/LLM Paper Briefing runner
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Support --legacy flag for rollback
if [ "${1:-}" = "--legacy" ]; then
    "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/daily_briefing_legacy.py" >> "$SCRIPT_DIR/logs/briefing.log" 2>&1
else
    "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/daily_briefing.py" "$@" >> "$SCRIPT_DIR/logs/briefing.log" 2>&1
fi
