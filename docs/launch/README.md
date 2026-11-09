# OncoAI — Google Play launch pack

> **OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.**

Draft documents for the first Google Play release of the OncoAI Android app (`com.oncoai.app`).
All files here are drafts: anything in `[SQUARE BRACKETS]` must be filled in by the owner, and
the legal texts should be reviewed by a qualified lawyer before publication.

| # | Document | Status |
|---|----------|--------|
| 1 | [Privacy policy](01-privacy-policy.md) | Draft, based on the API contract and backend code on `oncoai-platform` (commit `96a70bb`) |
| 2 | [Play Store listing copy](02-play-store-listing.md) | Draft |
| 3 | [Data Safety form](03-data-safety-form.md) | Draft answers checked against the Android build at `55d1bac`. Three answers depend on fixes (photo permission, EXIF, web deletion page) |
| 4 | [Health and medical device policy review](04-health-policy-review.md) | Draft. **Read this first:** it lists product changes needed before submission |
| 5 | [Release checklist](05-release-checklist.md) | Draft |

## What these drafts are based on

- `docs/API_CONTRACT.md` (v1) on branch `oncoai-platform`
- Backend code: `backend/app/core/config.py`, `backend/app/services/storage.py`, `backend/app/api/v1/users.py`, `backend/app/models/*`
- Frontend: `frontend/capacitor.config.ts`, `frontend/package.json`, `frontend/src/lib/native.ts`, `frontend/src/lib/storage.ts`, `frontend/src/lib/safety.ts`
- Google Play Policy Center pages *Health Content and Services* and *Understanding Google Play's app account deletion requirements*, read on 2026-11-09

The first drafts were written against `96a70bb`. The Data Safety form, privacy policy, policy review
and release checklist were then updated against `55d1bac`, which added the Android project and the
community, moderation and assistant backends. Re-check every document against the final release
build before submission.

No files outside `docs/launch/` were changed.
