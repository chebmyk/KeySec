#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
    printf '%s\n' "build-wheel-macos-arm64.sh: this script requires a macOS ARM64 host." >&2
    exit 1
fi

PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    printf '%s\n' "build-wheel-macos-arm64.sh: Python 3 is required (set PYTHON to its executable)." >&2
    exit 1
fi

VENV_DIR="$SCRIPT_DIR/.venv"
"$PYTHON" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip build
mkdir -p "$REPO_ROOT/dist"
cd "$REPO_ROOT"
"$VENV_DIR/bin/python" -m build --wheel --outdir "$REPO_ROOT/dist"
