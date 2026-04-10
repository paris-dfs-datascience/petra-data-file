#!/bin/sh

set -eu

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "Python is required to configure Microsoft Entra app registrations." >&2
  exit 1
fi

exec "$PYTHON_BIN" ./scripts/entra/sync_apps.py --mode preprovision
