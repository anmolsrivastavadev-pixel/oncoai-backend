# Deploying the OncoAI backend

The backend is a container (`backend/Dockerfile`). It needs PostgreSQL, a persistent
disk for scan photos, and about 1.5 GB of RAM if the PyTorch model is enabled. That rules
out serverless function hosts such as Vercel; use a container host.

## Render (config included)

1. In Render: **New → Blueprint**, choose this repository. `render.yaml` creates the web
   service `oncoai-api`, the database `oncoai-db` and a 5 GB disk mounted at `/data`.
2. When prompted for secrets:
   * `IMAGE_ENCRYPTION_KEY`: generate one with
     `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
     Keep a copy somewhere safe; photos cannot be read without it.
   * `ANTHROPIC_API_KEY`: optional. Leave empty and the assistant answers from its built-in
     knowledge base.
3. Deploy. On start the container runs `alembic upgrade head`, downloads the scan model to
   the disk on first boot (about 330 MB), and serves on Render's `PORT`.
4. Check `https://<your-service>.onrender.com/health`. It should report `"db":"ok"` and
   `"kind":"vit"`.
5. Point the app at it: set `VITE_API_URL=https://<your-service>.onrender.com` in
   `frontend/.env.android`, then `ONCOAI_RELEASE=1 npm run build:android` and rebuild the APK.
6. Make yourself a moderator from the Render shell:
   `python scripts/create_admin.py you@example.com --role admin`.
7. Disconnect the old Vercel project from this repository (Vercel → Project → Settings →
   Git → Disconnect) so it stops reporting failed deployments.

Costs: the `standard` web plan, the `basic-256mb` database and the disk are all paid
Render resources. To run on a smaller plan set `ANALYZER_KIND=heuristic` and
`FETCH_MODEL=0`; scans then use the computer-vision analysis without the neural model.

## Any other container host (Fly.io, Railway, a VPS)

Build `backend/`, provide the environment variables from `backend/.env.example`, mount a
volume at `/data`, and expose the port in `PORT` (default 8000). `docker-compose.yml`
shows the full set-up including PostgreSQL. Put HTTPS in front of it; the Android app
blocks cleartext traffic to anything except the emulator loopback.

## Operational notes

* Back up the database and the `/data/uploads` volume together.
* The rate limiter is in-memory, so run a single instance or move limits to the gateway.
* `SECRET_KEY` rotation logs everyone out; `IMAGE_ENCRYPTION_KEY` must not be rotated
  without re-encrypting stored photos.
