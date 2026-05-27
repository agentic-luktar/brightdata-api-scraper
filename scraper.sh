#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
VERSION_CACHE="$SCRIPT_DIR/.last_installed_version"
CURRENT_VERSION=$(grep -E '^__version__' "$SCRIPT_DIR/scraper/__init__.py" | sed 's/.*"\(.*\)".*/\1/')

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Install requirements only when version has changed
LAST_VERSION=""
if [ -f "$VERSION_CACHE" ]; then
    LAST_VERSION=$(cat "$VERSION_CACHE")
fi

if [ "$CURRENT_VERSION" != "$LAST_VERSION" ]; then
    echo "Version changed ($LAST_VERSION -> $CURRENT_VERSION), installing requirements..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
    echo "$CURRENT_VERSION" > "$VERSION_CACHE"
fi

python -m scraper "$@"
