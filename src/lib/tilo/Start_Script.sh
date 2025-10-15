#!/usr/bin/env sh
set -eu

PYTHON=${PYTHON3:-/usr/bin/python3}

# Default to the button-in-window test if no args were given
if [ "$#" -eq 0 ]; then
  set -- --run-in-window
fi

exec "$PYTHON" -u /usr/lib/tilo/Tilo.py "$@"
