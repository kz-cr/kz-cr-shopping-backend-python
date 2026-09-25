#!/usr/bin/env bash
#
# Set up and start the gallery backend locally. Creates the virtualenv,
# installs dependencies, seeds the database and starts the server.
#
# Safe to re-run: every step is skipped when it is already done.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5000}"
VENV_DIR="${VENV_DIR:-.venv}"
PYTHON="${PYTHON:-python3}"
MIN_PYTHON="3.9"

RESET_DB=0
FETCH_IMAGES=0
SETUP_ONLY=0
DEBUG=0

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'USAGE'
Set up and start the gallery backend locally.

Usage: ./run.sh [options]

  --reset           drop and reseed the database first
  --fetch-images    re-download the catalogue images first (needs network)
  --setup-only      do the setup, do not start the server
  --debug           enable the reloader and the Flask debugger
  --host HOST       bind address (default 127.0.0.1)
  --port PORT       bind port (default 5000)
  -h, --help        show this message

Environment: HOST, PORT, VENV_DIR, PYTHON, FLASK_CONFIG, CORS_ORIGINS.

Examples:
  ./run.sh                     first run: set up everything, then serve
  ./run.sh --debug             serve with auto-reload while developing
  ./run.sh --reset             reload the catalogue from app/catalog.py
  ./run.sh --setup-only        prepare the checkout without serving
USAGE
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --reset)        RESET_DB=1 ;;
        --fetch-images) FETCH_IMAGES=1 ;;
        --setup-only)   SETUP_ONLY=1 ;;
        --debug)        DEBUG=1 ;;
        --port)         [ $# -ge 2 ] || die "--port needs a value"; PORT="$2"; shift ;;
        --port=*)       PORT="${1#*=}" ;;
        --host)         [ $# -ge 2 ] || die "--host needs a value"; HOST="$2"; shift ;;
        --host=*)       HOST="${1#*=}" ;;
        -h|--help)      usage ;;
        *)              die "unknown option '$1' (try --help)" ;;
    esac
    shift
done

case "$PORT" in
    ''|*[!0-9]*) die "port must be a number, got '$PORT'" ;;
esac

# The Flask debugger executes arbitrary code from the browser, so it must never
# be reachable off this machine.
if [ "$DEBUG" -eq 1 ] && [ "$HOST" != "127.0.0.1" ] && [ "$HOST" != "localhost" ]; then
    die "refusing to run --debug on $HOST; the debugger allows remote code execution"
fi

# ---------------------------------------------------------------- interpreter

command -v "$PYTHON" >/dev/null 2>&1 \
    || die "'$PYTHON' not found; install Python $MIN_PYTHON+ or set PYTHON=/path/to/python3"

"$PYTHON" - "$MIN_PYTHON" <<'PY' || die "Python $MIN_PYTHON+ required; '$PYTHON' is older"
import sys
required = tuple(int(part) for part in sys.argv[1].split("."))
sys.exit(0 if sys.version_info[: len(required)] >= required else 1)
PY

# --------------------------------------------------------------------- venv

if [ ! -x "$VENV_DIR/bin/python" ]; then
    say "Creating virtualenv in $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
else
    say "Using existing virtualenv in $VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

# ---------------------------------------------------------------- dependencies

# Fetching images needs Pillow, which is a dev-only dependency.
REQUIREMENTS="requirements.txt"
[ "$FETCH_IMAGES" -eq 1 ] && REQUIREMENTS="requirements-dev.txt"

# The stamp is per requirements file, so switching between them reinstalls
# rather than silently reusing the wrong set. The development requirements
# include requirements.txt, so that file must also be current for its stamp.
STAMP="$VENV_DIR/.stamp-$(basename "$REQUIREMENTS")"

if [ ! -f "$STAMP" ] || [ "$REQUIREMENTS" -nt "$STAMP" ] \
    || { [ "$FETCH_IMAGES" -eq 1 ] && [ "requirements.txt" -nt "$STAMP" ]; }; then
    say "Installing dependencies from $REQUIREMENTS"
    "$VENV_PYTHON" -m pip install --quiet --upgrade pip
    "$VENV_PYTHON" -m pip install --quiet -r "$REQUIREMENTS"
    touch "$STAMP"
else
    say "Dependencies already installed"
fi

# --------------------------------------------------------------------- images

IMAGE_DIR="app/static/images"

if [ "$FETCH_IMAGES" -eq 1 ]; then
    say "Fetching catalogue images"
    "$VENV_PYTHON" scripts/fetch_images.py --force
elif [ "$(ls "$IMAGE_DIR"/*.jpg 2>/dev/null | wc -l)" -eq 0 ]; then
    warn "no images found in $IMAGE_DIR — the API will work but pictures will 404"
    warn "run './run.sh --fetch-images' to download them"
fi

# ------------------------------------------------------------------- database

if [ "$RESET_DB" -eq 1 ]; then
    say "Resetting the database"
    "$VENV_PYTHON" -m flask --app wsgi init-db --reset
else
    say "Preparing the database"
    "$VENV_PYTHON" -m flask --app wsgi init-db
fi

if [ "$SETUP_ONLY" -eq 1 ]; then
    say "Setup complete — start the server with ./run.sh"
    exit 0
fi

# ---------------------------------------------------------------------- serve

FLAGS=""
[ "$DEBUG" -eq 1 ] && FLAGS="--debug"

say "Serving on http://$HOST:$PORT — try /api/items, Ctrl-C to stop"
# shellcheck disable=SC2086  # FLAGS is a single optional flag, not a path
exec "$VENV_PYTHON" -m flask --app wsgi run --host "$HOST" --port "$PORT" $FLAGS
