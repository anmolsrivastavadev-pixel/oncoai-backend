#!/bin/sh
set -e
alembic upgrade head
if [ "${FETCH_MODEL:-0}" = "1" ]; then
  python scripts/fetch_model.py || echo "Model download failed; continuing with the heuristic analyzer."
fi
exec "$@"
