#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if [ "$(uname -s)" != "Linux" ]; then
    printf '%s\n' "build-executable-unix.sh: this script requires a Linux host." >&2
    exit 1
fi

PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    printf '%s\n' "build-executable-unix.sh: Python 3.10 or newer is required (set PYTHON to its executable)." >&2
    exit 1
fi

if ! command -v objdump >/dev/null 2>&1; then
    printf '%s\n' "build-executable-unix.sh: objdump is required; install the binutils package." >&2
    exit 1
fi

VENV_DIR="$SCRIPT_DIR/.venv"
"$PYTHON" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip PyInstaller "$REPO_ROOT"
mkdir -p "$REPO_ROOT/dist" "$REPO_ROOT/build/pyinstaller-spec" "$REPO_ROOT/build/pyinstaller-work"
cd "$REPO_ROOT"
"$VENV_DIR/bin/python" -m PyInstaller --noconfirm --clean --onefile --name keysec \
    --distpath "$REPO_ROOT/dist" \
    --workpath "$REPO_ROOT/build/pyinstaller-work" \
    --specpath "$REPO_ROOT/build/pyinstaller-spec" \
    "$REPO_ROOT/src/keysec/cli.py"
