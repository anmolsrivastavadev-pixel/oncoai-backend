#!/bin/sh
set -e

if [ "$(id -u)" = "0" ]; then
  mkdir -p "${UPLOAD_DIR:-/data/uploads}" "$(dirname "${MODEL_DIR:-/data/models/skin-lesion-vit}")"
  chown -R oncoai:oncoai /data 2>/dev/null || true
  exec setpriv --reuid=oncoai --regid=oncoai --init-groups "$0" "$@"
fi

alembic upgrade head
if [ "${FETCH_MODEL:-0}" = "1" ]; then
  python scripts/fetch_model.py || echo "Model download failed; continuing with the heuristic analyzer."
fi
exec "$@"
