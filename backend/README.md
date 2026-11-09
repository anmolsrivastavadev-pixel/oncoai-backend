# OncoAI backend

> OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.

FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL. API contract: [`../docs/API_CONTRACT.md`](../docs/API_CONTRACT.md).
Interactive docs at `/docs` when running.

## Setup without Docker

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# optional deep-learning model (CPU wheels are much smaller than the default CUDA ones):
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.15.0
pip install -r requirements-ml.txt
python scripts/fetch_model.py             # ~330 MB into ./models/skin-lesion-vit

createuser -P oncoai && createdb -O oncoai oncoai
cp .env.example .env                      # set SECRET_KEY, DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload             # http://localhost:8000
```

Tests need a second database: `createdb -O oncoai oncoai_test`, then
`pip install -r requirements-dev.txt && pytest -q` (override with `TEST_DATABASE_URL`).

Make a moderator or admin: `python scripts/create_admin.py you@example.com --role moderator`.

## Layout and why

```
app/core       config (pydantic-settings), JWT + bcrypt, rate limiter, security headers, logging
app/db         engine/session, declarative base with naming conventions (stable Alembic diffs)
app/models     SQLAlchemy 2 typed models          app/schemas   Pydantic request/response models
app/api/v1     one router per feature; deps.py holds auth/role/pagination dependencies
app/services   storage (images), scan_service, booking, moderation, seed, assistant/
app/ml         cv_features (OpenCV), vit_analyzer (transformers), heuristic_analyzer, concern
alembic        migrations (CI fails if models and migrations drift)
```

* **Routers stay thin, services hold logic.** The same service functions are used by
  routes and tests, and the ML code knows nothing about HTTP or the database.
* **JWT access + refresh tokens.** Access tokens live 30 minutes; a `type` claim stops a
  refresh token being used as an access token and vice versa. Passwords are bcrypt hashes.
  The app refuses to start in production with a missing or default `SECRET_KEY`.
* **Analyzer interface.** `ViTAnalyzer` and `HeuristicAnalyzer` implement one protocol.
  `ANALYZER_KIND=auto` uses the model when a checkpoint and `torch` are present and
  otherwise falls back to CV-only analysis; `/health` reports which one is live.
* **Concern score.** `0.6 × model score + 0.4 × CV score` (CV only in heuristic mode),
  plus bounded bumps for reported symptoms such as bleeding or change. Under 35 is low,
  under 65 moderate, otherwise higher. Poor photo quality floors the result at moderate.
  Only fixed, educational sentences are returned; model labels stay in a private audit
  column and are never serialised.
* **Protected images.** Uploads are fully decoded with Pillow (not trusted by extension
  or MIME type), size and pixel limits applied, EXIF orientation fixed and then all
  metadata stripped (GPS included) by re-encoding. Files live outside any static
  directory under random names and are only served through an authenticated,
  owner-checked endpoint with `Cache-Control: private, no-store`. Set
  `IMAGE_ENCRYPTION_KEY` to encrypt them at rest. Deleting a scan, a spot or the account
  deletes the files.
* **Assistant.** Deterministic input guardrails (diagnosis requests, treatment or
  medication requests, urgent symptoms, self-harm) answer before any model is called. With
  `ANTHROPIC_API_KEY` set, Claude answers using retrieved knowledge-base notes under a
  strict system prompt, and an output filter replaces any reply containing diagnostic or
  treatment language. Without a key the curated knowledge base answers directly.
* **Community.** Posts and comments containing emails or phone numbers are rejected,
  profanity is masked, anonymous posting is supported, and content with three open
  reports is hidden until a moderator reviews it.
* **Sample data.** The seeded dermatologists are fictional and flagged `is_sample`.
  Replace them with real, consented listings before launch (`SEED_SAMPLE_DATA=false`).

## Environment variables

See [`.env.example`](.env.example). The important ones: `DATABASE_URL`, `SECRET_KEY`,
`ENVIRONMENT`, `CORS_ORIGINS`, `UPLOAD_DIR`, `IMAGE_ENCRYPTION_KEY`, `MODEL_DIR`,
`ANALYZER_KIND`, `MODEL_LABEL_WEIGHTS` (JSON), `ANTHROPIC_API_KEY`, `ASSISTANT_MODEL`,
`RATE_LIMIT_ENABLED`.

## Swapping the scan model

Any Hugging Face image-classification checkpoint works. Put it in a folder, set
`MODEL_DIR`, and set `MODEL_LABEL_WEIGHTS` to a JSON object mapping the class names that
should raise the score to a weight between 0 and 1, for example
`{"melanoma": 1.0, "basal_cell_carcinoma": 1.0, "actinic_keratoses": 0.6}`. The server
refuses a model none of whose labels match, rather than silently scoring everything 0.
`scripts/train_classifier.py` fine-tunes a model on an image-folder dataset; read its
header about lesion-level splits before trusting its validation accuracy.

## Known limits

* The rate limiter is in-memory, so it is per process. Use Redis or a gateway limiter when
  running more than one worker.
* Reminders are stored and shown in the app and scheduled as local notifications on the
  phone; the backend does not send email or push notifications.
* See the root README for the limits of the scan model.
