# Deploying to Render (free tier)

This is the actual path this repo is deployed with — a plain **Web Service**,
set up by hand in the dashboard, no paid Blueprint resources involved.

## 1. Push this repo to GitHub

Render deploys from a git remote.

```bash
git remote add origin <your-github-repo-url>
git push -u origin main
```

## 2. Create the Web Service

1. Render dashboard → **New** → **Web Service**.
2. Connect this GitHub repo.
3. Set:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash render-start.sh`
   - **Plan**: Free
4. Under **Environment**, add:
   - `SECRET_KEY` — any random string (e.g. generate one with `python -c "import secrets; print(secrets.token_hex(32))"`)
5. Click **Create Web Service**.

That's it — no `DATABASE_URL` needed to start; the app falls back to SQLite
automatically when it's unset.

## 3. (Optional) Add a free Postgres database

The free plan has no persistent disk, so the ephemeral filesystem — and
anything on it, including a SQLite file — is reset on every restart or
redeploy. Free Web Services also spin down after ~15 minutes idle and
cold-start fresh on the next request, so this happens often.

To keep your actual data (patients, scans, predictions, accounts) across
restarts without paying for a disk:

1. Render dashboard → **New** → **PostgreSQL** → pick the **Free** plan.
2. Once it's created, copy its **Internal Database URL**.
3. Back on the web service → **Environment** → add `DATABASE_URL` set to
   that value.
4. Redeploy.

This only covers the database. Uploaded scan images and hero slider photos
still live on the web service's own ephemeral filesystem and will not
survive a restart on the free plan — there's no free way around that
short of external object storage (e.g. S3), which isn't set up here.

## 4. Seed the database (optional)

Open a shell for the service in the Render dashboard and run:

```bash
flask --app run.py seed-db
```

Skip this if you'd rather start empty and register the first account at
`/auth/register`.

## A real risk on the free plan: memory

torch + transformers + ultralytics need real RAM once the classification
and segmentation models are loaded. Render's free plan gives the service
512MB. This may not be enough — if it isn't, you'll see the service get
killed (an out-of-memory error) right after the first scan upload, not at
build time. If that happens, the only real fix is a paid plan with more
RAM (Standard or higher).

`render-start.sh` runs a single gunicorn worker on purpose regardless of
plan: each worker loads its own copy of the ML models into memory, so more
workers means proportionally more RAM.

## Local development is unaffected

Locally, `DATABASE_URL` is unset, so the app keeps using SQLite at
`instance/app.db`, and uploads stay directly under `app/static/uploads/` —
none of the above changes what `flask run` does on your machine.

---

## Alternative: paid Blueprint deploy

If you later want persistence for uploads *and* model weight caching
without doing the disk/Postgres wiring by hand, this repo also has a
`render.yaml` Blueprint that provisions a paid web service plan, a paid
persistent disk, and a Postgres database together in one step (**New** →
**Blueprint** in the Render dashboard, pointed at this repo). It is not
used by the free-tier setup above — `render.yaml` is only read for
Blueprint deployments.
