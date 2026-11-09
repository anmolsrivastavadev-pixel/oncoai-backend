# OncoAI

**Scan. Track. Stay Informed.**

> OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.

OncoAI is an Android app (React + Capacitor) with a FastAPI backend. People photograph a
skin spot, get an *educational* summary of its visual features (low / moderate / higher
concern), track spots over time, book a dermatologist, talk to a supportive community and
ask an educational assistant questions. It never names a disease, never recommends
treatment and never presents itself as a replacement for a doctor.

```
backend/    FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, JWT, PyTorch + OpenCV scan pipeline
frontend/   React 18 + TypeScript + Tailwind + Framer Motion, wrapped with Capacitor 6
frontend/android/   The Android Studio / Gradle project (package com.oncoai.app)
docs/API_CONTRACT.md   The API both sides are built against
docker-compose.yml     PostgreSQL + backend
```

## Quick start

### 1. Backend

```bash
cp backend/.env.example backend/.env      # set SECRET_KEY
docker compose up --build                 # API on http://localhost:8000, docs at /docs
```

The first start downloads the scan model (about 330 MB) into a Docker volume. Set
`FETCH_MODEL=0` to skip it; the API then uses the computer-vision-only analyzer.
Without Docker: see [backend/README.md](backend/README.md). To host it: [docs/DEPLOY.md](docs/DEPLOY.md) (Render config included).

### 2. Web app (for development)

```bash
cd frontend
npm ci
cp .env.example .env                      # VITE_API_URL=http://localhost:8000
npm run dev                               # http://localhost:5173
```

### 3. Android app

Requires Android Studio (or the Android SDK with platform 34) and JDK 17+.

```bash
cd frontend
npm ci
npm run build:android                     # builds web assets with .env.android and syncs them
cd android && ./gradlew assembleDebug     # app/build/outputs/apk/debug/app-debug.apk
# or: npx cap open android  → Run in Android Studio
```

`.env.android` points the app at `http://10.0.2.2:8000`, which is the host machine as seen
from the Android **emulator**. For a physical phone set `VITE_API_URL` to an HTTPS URL of
your deployed backend (cleartext HTTP is blocked for everything except the emulator
loopback, see `android/app/src/main/res/xml/network_security_config.xml`) and add that
origin to the backend's `CORS_ORIGINS` if you also serve the web app from it.

Every push also builds the debug APK in GitHub Actions (workflow **CI**, artifact
`oncoai-debug-apk`).

## The phases

| Phase | What | Where |
|---|---|---|
| 1 Foundation | Folder structure, config, DB, auth architecture, UI kit | `backend/app/{core,db,models,schemas}`, `frontend/src/{lib,components/ui}` |
| 2 Landing | Hero, branding, CTAs, animated scan visual | `frontend/src/features/landing` |
| 3 Auth | Signup/login, bcrypt, JWT access + refresh, protected routes, profile | `backend/app/api/v1/{auth,users}.py`, `frontend/src/features/auth` |
| 4 AI scan | Camera/gallery capture, preview, upload, analysis, concern levels | `backend/app/ml`, `backend/app/services/scan_service.py`, `frontend/src/features/scan` |
| 5 Tracking | Lesion history, timeline, symptoms, side-by-side compare, charts | `backend/app/api/v1/tracking.py`, `frontend/src/features/tracking` |
| 6 Booking | Dermatologist search, slots, booking, reminders | `backend/app/api/v1/{dermatologists,appointments,reminders}.py`, `frontend/src/features/care` |
| 7 Community | Feed, posts, comments, support reactions, reports, moderation | `backend/app/api/v1/{community,moderation}.py`, `frontend/src/features/community` |
| 8 Assistant | Chat UI, educational knowledge base, optional Claude, guardrails | `backend/app/services/assistant`, `frontend/src/features/assistant` |
| 9 Polish & security | Rate limits, security headers, protected images, skeletons, offline banner | throughout |

## What the scan is, and is not

* The pipeline combines classic computer-vision measurements (asymmetry, border
  irregularity, colour variation, relative size) with an optional image classifier
  (PyTorch / Hugging Face `transformers`, CPU).
* The default checkpoint is [`Anwarkh1/Skin_Cancer-Image_Classification`](https://huggingface.co/Anwarkh1/Skin_Cancer-Image_Classification)
  (ViT-base, Apache-2.0, fine-tuned on HAM10000). Its class names and probabilities are
  used only internally to compute a 0–100 "visual concern score". **They are never
  returned by the API or shown in the app.**
* **Limits, stated plainly.** HAM10000 is *dermoscopy* imagery; ordinary phone photos are
  out of distribution, so the model is less reliable on them. The accuracy figure on the
  model card is the author's own and has not been independently validated, and that
  dataset under-represents darker skin tones. OncoAI has had no clinical validation and
  is not a medical device. A "low concern" result does not mean a spot is harmless, which
  is why every result tells people to see a professional about anything new, changing or
  worrying.
* A sanity check on 40 public ISIC dermoscopy images (20 labelled melanoma, 20 labelled
  nevus) put 14/20 and 4/20 respectively in "higher concern", and 2/20 and 12/20 in "low".
  Those images very likely overlap the model's training data, so this shows the pipeline
  runs end to end and nothing more. It is not an accuracy estimate.
* Poor-quality photos are never given a reassuring result: they are floored at
  "moderate" with advice to retake the photo.
* To use a better model, train or download one and point `MODEL_DIR` at it
  (`backend/scripts/train_classifier.py`, `backend/scripts/fetch_model.py`).

## Before a public launch

This codebase is production-style, but shipping a health app to the public needs more
than code: a privacy policy and data-processing basis for health photos (GDPR / UK GDPR /
India DPDP), Google Play's health-app declarations, a regulatory view on whether your
marketing claims make it a medical device, real dermatologist listings (the seeded ones
are fictional and flagged "Sample listing"), human moderators for the community, HTTPS
hosting with backups, and a release signing key.

## Verification

```bash
cd backend  && ruff check . && pytest -q            # API, security, ML and guardrail tests (needs PostgreSQL)
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
node frontend/e2e/full-flow.mjs <photo.jpg>         # real-browser run against a live backend
```
