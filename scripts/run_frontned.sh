#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
echo "run_frontned.sh is retained for compatibility; use run_frontend.sh."
exec "$SCRIPT_DIR/run_frontend.sh"
