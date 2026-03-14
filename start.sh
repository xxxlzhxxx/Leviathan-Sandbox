#!/bin/bash
set -e

# Auto-detect venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if leviathan-sandbox is installed
if ! command -v leviathan-sandbox &> /dev/null; then
    echo "❌ Leviathan Sandbox not installed or venv not activated."
    echo "   Run './install.sh' first."
    exit 1
fi

# Pass all arguments to the CLI
leviathan-sandbox "$@"
