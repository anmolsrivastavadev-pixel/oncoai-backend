# OncoAI — Play Data Safety form (ON HOLD)

> **OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.**

**Status: on hold until the Android app code (`frontend/android/`) is pushed.** The owner asked for
the Data Safety answers to wait until they can be checked against the actual build. This file sets
out the form's structure and lists exactly what to check. **None of the answers below are final, and
they must not be entered into the Play Console as they stand.**

The Data Safety answers must match the privacy policy ([01-privacy-policy.md](01-privacy-policy.md))
and what the app actually does, including every bundled SDK. Google checks these against the build.

---

## A. Verify against the code first

Check each item in the pushed code and record the result here.

| # | Check | Where to look | Result |
|---|---|---|---|
| 1 | Final list of SDKs and libraries in the release AAB (analytics, crash reporting, push, ads, attribution) | `frontend/android/app/build.gradle`, `frontend/package.json`, merged manifest | _pending_ |
| 2 | Permissions in the merged manifest (expected: `CAMERA`, `POST_NOTIFICATIONS`, `INTERNET`, `SCHEDULE_EXACT_ALARM`/`USE_EXACT_ALARM`?, `READ_MEDIA_IMAGES`?) | `frontend/android/app/src/main/AndroidManifest.xml` + merged manifest report | _pending_ |
| 3 | Gallery access uses the system Photo Picker, not a broad media permission | `@capacitor/camera` config | _pending_ |
| 4 | All network traffic is HTTPS in release (`ONCOAI_RELEASE=1`, no `allowMixedContent`, production `VITE_API_URL` is `https://`) | `capacitor.config.ts`, release env, network security config | _pending_ |
| 5 | `IMAGE_ENCRYPTION_KEY` is set in production | Deployment config | _pending_ |
| 6 | Assistant: is the Anthropic API enabled in production? What is sent? Is chat history stored server-side? | `backend/app/api/v1/assistant.py` (not yet implemented) | _pending_ |
| 7 | Community: what is stored for anonymous posts? | `backend/app/api/v1/community.py` (not yet implemented) | _pending_ |
| 8 | Appointment requests: are they sent to any clinic or third party? | `backend/app/services/booking.py` | _pending_ |
| 9 | `DELETE /users/me` removes every data type declared as collected, including community content and files | `backend/app/api/v1/users.py`, model cascades, `storage.delete_user_files` | Cascades and file deletion are present in the code on `96a70bb`. Retest once community is implemented |
| 10 | Web deletion page is live | [https://oncoai.app/delete-account] | _pending_ |
| 11 | Are photos or health data ever used for model training or analytics? | Backend services | _pending_ |
| 12 | Are IP addresses or logs kept beyond transient rate limiting? | `backend/app/core/rate_limit.py`, logging config | _pending_ |

## B. Form structure (fill in after section A)

### B1. Data collection and security
- Does the app collect or share any of the required user data types? — _pending (expected: Yes)_
- Is all user data collected by the app encrypted in transit? — _pending (depends on check 4)_
- Do you provide a way for users to request that their data is deleted? — _pending (expected: Yes, in-app + web URL)_
- Account deletion URL — `[https://oncoai.app/delete-account]`

### B2. Data types
For each data type: **collected?**, **shared?**, **processed ephemerally?**, **required or
optional?**, and **purposes** (App functionality, Analytics, Developer communications, Advertising
or marketing, Fraud prevention/security/compliance, Personalization, Account management).

| Play category → data type | Candidate source in OncoAI | Answers |
|---|---|---|
| Personal info → Name | `full_name` | _pending_ |
| Personal info → Email address | `email` | _pending_ |
| Personal info → User IDs | account ID | _pending_ |
| Personal info → Other info | date of birth, skin type, location text, bio | _pending_ |
| Health and fitness → Health info | spots, symptoms, scan feature results, appointments, health notes | _pending_ |
| Photos and videos → Photos | skin photos | _pending_ |
| Messages → Other in-app messages | community posts/comments, assistant chats | _pending_ |
| App activity → Other user-generated content | community content, reports | _pending_ |
| App info and performance → Crash logs / Diagnostics | only if an SDK or server logging qualifies (check 1, 12) | _pending_ |
| Device or other IDs | only if an SDK collects them (check 1) | _pending_ |
| Location | not expected (EXIF GPS is stripped server-side, but check whether stripping counts as "collected" when the original upload contains it) | _pending_ |

"Shared" candidates to assess: the AI assistant provider (check 6) and clinics (check 8). Under
Play's definitions, sending data to a service provider that processes it on your behalf is not
"sharing". Confirm this applies, and that the provider's terms support it.

---

*OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or
treatment advice.*
