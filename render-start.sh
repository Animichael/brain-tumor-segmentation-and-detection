#!/usr/bin/env bash
# Render start command: puts uploaded scan/slider images and the
# Hugging Face model cache on the attached persistent disk (so they survive
# restarts and redeploys), then boots the app under gunicorn.
#
# Uploaded images are kept reachable at their normal app/static/uploads/ URL
# by symlinking that path to the persistent disk — no route or template
# changes needed.
set -euo pipefail

DATA_DIR="${RENDER_DISK_PATH:-/var/data}"

mkdir -p "$DATA_DIR/uploads/scans" "$DATA_DIR/uploads/slider" "$DATA_DIR/hf-cache"

if [ ! -L app/static/uploads ]; then
    # First boot on this disk: seed it with whatever shipped in the repo
    # (sample MRIs, hero slider photos) before switching to the symlink.
    cp -rn app/static/uploads/. "$DATA_DIR/uploads/" 2>/dev/null || true
    rm -rf app/static/uploads
    ln -s "$DATA_DIR/uploads" app/static/uploads
fi

export HF_HOME="$DATA_DIR/hf-cache"

exec gunicorn run:app \
    --bind "0.0.0.0:${PORT:-10000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --timeout 300
