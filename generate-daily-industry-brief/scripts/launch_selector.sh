#!/bin/sh
# launch_selector.sh - locate a Python >= 3.6 interpreter and run launch_selector.py
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SCRIPT="$SCRIPT_DIR/launch_selector.py"

version_ok() {
    "$1" -c "import sys;sys.exit(0 if sys.version_info>=(3,6) else 1)" >/dev/null 2>&1
}

TRIED=""
for candidate in python3 python \
    "$HOME/opt/anaconda3/bin/python3" "$HOME/anaconda3/bin/python3" \
    "$HOME/opt/miniconda3/bin/python3" "$HOME/miniconda3/bin/python3" \
    "$HOME/anaconda3/python.exe" "$HOME/miniconda3/python.exe"; do
    TRIED="$TRIED $candidate;"
    case "$candidate" in
        */*)
            [ -f "$candidate" ] || continue
            ;;
        *)
            command -v "$candidate" >/dev/null 2>&1 || continue
            ;;
    esac
    if version_ok "$candidate"; then
        exec "$candidate" "$SCRIPT" "$@"
    fi
done

echo "[launch_selector] ERROR: no Python interpreter with version 3.6 or newer was found." >&2
echo "[launch_selector] Tried:$TRIED" >&2
echo "[launch_selector] Install Python 3.6+ or add it to PATH, then retry." >&2
exit 4
