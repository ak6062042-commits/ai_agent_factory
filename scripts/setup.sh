#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
else
    PYTHON_BIN=python
fi

cd "$PROJECT_ROOT"

if [ ! -d "$VENV_PATH" ]; then
    "$PYTHON_BIN" -m venv "$VENV_PATH"
fi

"$VENV_PATH/bin/python" -m pip install --upgrade pip
"$VENV_PATH/bin/python" -m pip install -r requirements.txt

echo "Setup complete. Activate the environment with: source .venv/bin/activate"