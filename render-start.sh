#!/usr/bin/env bash
# Render start command for a plain (free-tier) Web Service — no persistent
# disk attached. Uploaded scans, the SQLite DB (if used), and the Hugging
# Face model cache all live on the service's own ephemeral filesystem, which
# is reset on every restart/redeploy. If you later attach a paid disk, point
# RENDER_DISK_PATH at its mount path to make these persist instead.
set -euo pipefail

mkdir -p app/static/uploads/scans app/static/uploads/slider

if [ -n "${RENDER_DISK_PATH:-}" ]; then
    mkdir -p "$RENDER_DISK_PATH/hf-cache"
    export HF_HOME="$RENDER_DISK_PATH/hf-cache"
fi

exec gunicorn run:app \
    --bind "0.0.0.0:${PORT:-10000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --timeout 300
