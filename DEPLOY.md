# Deploying to Render

This repo includes a `render.yaml` Blueprint, so Render can provision everything
(web service + Postgres database + persistent disk) in one step.

## 1. Push this repo to GitHub

Render deploys from a git remote (GitHub, GitLab, or Bitbucket). If you haven't
already:

```bash
git remote add origin <your-empty-github-repo-url>
git push -u origin main
```

## 2. Create the Blueprint on Render

1. Go to the Render dashboard → **New** → **Blueprint**.
2. Connect the GitHub repo you just pushed to.
3. Render reads `render.yaml` and shows you the plan: a web service
   (`neuroscan-ai`), a free Postgres database (`neuroscan-ai-db`), and a 5 GB
   persistent disk. Click **Apply**.
4. First deploy takes a while — it installs torch/transformers/ultralytics
   and downloads the ML model weights on the first upload.

`SECRET_KEY` is auto-generated and `DATABASE_URL` is wired to the Postgres
instance automatically; you don't need to set either by hand.

## 3. Seed the database (optional)

To get the demo admin account, hero slider images, and sample data, open a
shell for the service in the Render dashboard and run:

```bash
flask seed-db
```

Skip this if you'd rather start with an empty database and register the
first account yourself at `/auth/register`.

## Why a "Standard" plan

`render.yaml` requests Render's **Standard** plan (not the free/starter web
service tier). torch + transformers + ultralytics need real memory once the
classification and segmentation models are loaded — a 512MB instance will
likely be killed (OOM) on the first scan upload. If you want to try a smaller
plan anyway, edit the `plan:` line in `render.yaml`, but expect the first
upload after each restart to be slow or to fail under memory pressure.

`render-start.sh` runs a single gunicorn worker on purpose: each worker
loads its own copy of the ML models into memory, so more workers means
proportionally more RAM. Only raise `WEB_CONCURRENCY` (an env var on the
service) if you've also moved to a plan with the RAM to back it.

## Where things persist

- **Database**: the managed Postgres instance (`neuroscan-ai-db`) — backed
  up and independent of the web service's filesystem.
- **Uploaded scans & hero slider images**: the attached disk, mounted at
  `/var/data` and symlinked to `app/static/uploads` on boot (see
  `render-start.sh`) — survives restarts and redeploys.
- **Downloaded model weights**: cached on the same disk under
  `/var/data/hf-cache`, so they're only downloaded once, not on every
  restart.

## Local development is unaffected

Locally, `DATABASE_URL` is unset, so the app keeps using SQLite at
`instance/app.db`, and uploads stay directly under `app/static/uploads/` —
none of the above changes what `flask run` does on your machine.
