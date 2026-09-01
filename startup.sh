#!/usr/bin/env bash
# Container entrypoint for the Hugging Face Space.
#
# HF's free tier has no persistent disk, so the SQLite database starts empty
# on every build and every wake-from-sleep. Seed it (admin account,
# testimonials, sample patients) only when it has no users yet, so a restart
# that *does* keep the file doesn't try to insert a duplicate admin.
set -euo pipefail

mkdir -p app/static/uploads/scans app/static/uploads/slider instance

python - <<'PY'
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    if User.query.first() is None:
        from app.seed import seed_database
        seed_database()
        print(">> database seeded")
    else:
        print(">> database already has users, skipping seed")
PY

exec gunicorn run:app \
    --bind "0.0.0.0:${PORT:-7860}" \
    --workers 1 \
    --timeout 300
