# OncoAI — Play Data Safety form (draft answers)

> **OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.**

These draft answers are checked against `oncoai-platform` at **`55d1bac`** ("Add Android (Capacitor)
project…"). They must match the privacy policy ([01-privacy-policy.md](01-privacy-policy.md)) and the
**final release build**. Re-run section A whenever a dependency, permission or data flow changes.
Three answers depend on fixes that haven't been made yet. Those are marked **⚠ depends on fix**.

---

## A. Verification results

| # | Check | Finding at `55d1bac` | Effect on the form |
|---|---|---|---|
| 1 | Third-party SDKs | `app/build.gradle` plus `capacitor.build.gradle`: AndroidX, Capacitor core, and the Capacitor plugins camera, haptics, local-notifications, preferences, splash-screen and status-bar. **No analytics, crash-reporting, ads, attribution or Firebase.** `google-services.json` is absent, so the Google Services plugin isn't applied | No SDK data collection to declare. **Re-check if Firebase or Crashlytics is ever added** |
| 2 | Manifest permissions | `INTERNET`, `CAMERA`, `READ_MEDIA_IMAGES`, `READ_EXTERNAL_STORAGE` (maxSdk 32), `POST_NOTIFICATIONS`. No exact-alarm or location permissions | See check 3 |
| 3 | Gallery access | `READ_MEDIA_IMAGES` is declared. Under Play's *Photo and Video Permissions* policy, apps that need photos only once or occasionally must use the **system photo picker** and must not request `READ_MEDIA_IMAGES` | **⚠ depends on fix:** remove `READ_MEDIA_IMAGES` (and `READ_EXTERNAL_STORAGE`) and rely on the photo picker. Otherwise you have to file a permissions declaration, which is likely to be rejected for this use |
| 4 | Encryption in transit | `network_security_config.xml`: `cleartextTrafficPermitted="false"` by default, with an exception only for `10.0.2.2` and `localhost` (dev). The release must use an `https://` `VITE_API_URL` and `ONCOAI_RELEASE=1` | **Yes**, provided the release API is HTTPS. Recommended: drop the dev exceptions in release builds |
| 5 | `IMAGE_ENCRYPTION_KEY` in production | Still optional in `config.py` | Not a Data Safety question, but the privacy policy promises encryption at rest. **⚠ depends on fix / deploy config** |
| 6 | Assistant | `services/assistant/service.py` + `claude_provider.py`: if `ANTHROPIC_API_KEY` is set, the **last 12 chat messages** and, if the user attaches a scan, a text summary of the **concern level, score and visual measurements** (no image, name or email) are sent to Anthropic. **Chats are not stored** in the database. Logs record only the guardrail reason | Messages: collected, **processed ephemerally**. Anthropic acts as a **service provider**, so this is **not "shared"** under Play's definition |
| 7 | Community anonymity | `api/v1/community.py`: anonymous posts are shown as `ANONYMOUS_NAME` with `id: null`, but `user_id` is stored | Community content is collected and linked to the user |
| 8 | Appointment booking | `services/booking.py`: no outbound calls. Appointments are stored in OncoAI's database only, and not sent to any clinic | Not shared |
| 9 | Account deletion | `DELETE /users/me` deletes the user. Every user-owned table (posts, comments, reactions, reports, scans, lesions, symptom logs, reminders, appointments) uses `ondelete="CASCADE"`, and `storage.delete_user_files` removes photos. The frontend `ProfilePage.tsx` calls it | **In-app deletion: yes.** The web deletion page is still needed (check 10) |
| 10 | Web deletion page | Not yet created | **⚠ depends on fix:** publish `[https://oncoai.app/delete-account]` before submitting |
| 11 | Training or analytics use of photos and health data | No code paths found that export photos or health data, or use them for training | Purposes are limited to app functionality (and security for UGC). Keep it that way, or update the policy and form |
| 12 | IP addresses and logs | `rate_limit.py` keeps IPs **in memory only** (sliding window, single process). The access log (`middleware.py`) records method, path, status and duration, but **no IP and no user ID** | IP addresses are not a Play data type, so nothing to declare. Note them in the privacy policy (already done) |

Other things found in the build (not Data Safety questions; listed in the release checklist):
`targetSdkVersion 34` is below the current Play requirement. `minifyEnabled false`.
`versionName "1.0"` doesn't match `package.json` `1.0.0`. There's no privacy policy link in the app.
The assistant's system prompt and scan context still refer to concern levels and scores (policy
review 3.1).

---

## B. Answers to enter in Play Console

### B1. Data collection and security

| Question | Answer |
|---|---|
| Does your app collect or share any of the required user data types? | **Yes** |
| Is all of the user data collected by your app encrypted in transit? | **Yes** (HTTPS-only release API, see check 4) |
| Do you provide a way for users to request that their data be deleted? | **Yes**. In-app: Profile → Delete account. Web: `[https://oncoai.app/delete-account]` **⚠ page must be live** |
| Account deletion URL | `[https://oncoai.app/delete-account]` |
| Can users request that some data is deleted without deleting their account? | **Yes**: individual photos/scans, spots, reminders, appointments, posts and comments can each be deleted in the app |
| Has your app been independently validated against a global security standard (e.g. MASA)? | **No** (unless you commission a MASA assessment) |
| Is your app in the Families program? | **No** (18+) |

### B2. Data types

None of the data below is **shared** with third parties. The only external recipient is the AI
assistant provider, which acts as a service provider. Nothing is used for advertising, marketing,
analytics or personalisation.

| Category → Data type | Collected | Shared | Ephemeral | Required / optional | Purposes |
|---|---|---|---|---|---|
| **Personal info → Name** | Yes | No | No | Required (sign-up `full_name`) | App functionality, Account management |
| **Personal info → Email address** | Yes | No | No | Required | Account management, App functionality |
| **Personal info → User IDs** | Yes | No | No | Required (account ID) | App functionality, Account management |
| **Personal info → Other info** (date of birth, bio) | Yes | No | No | Optional | App functionality |
| **Location → Approximate location** (free-text "location" profile field, e.g. a city) | Yes | No | No | Optional | App functionality |
| **Location → Precise location** | **No** ⚠ depends on fix (see note 1) | — | — | — | — |
| **Health and fitness → Health info** (tracked spots, body locations, notes, symptoms, scan measurements, skin type, appointments) | Yes | No | No | Optional | App functionality |
| **Photos and videos → Photos** (skin photos) | Yes | No | No | Optional | App functionality |
| **Messages → Other in-app messages** (assistant chat) | Yes | No | **Yes** (not stored, see check 6) | Optional | App functionality |
| **App activity → Other user-generated content** (community posts, comments, reactions, reports) | Yes | No | No | Optional | App functionality, Fraud prevention, security and compliance (moderation) |
| App activity → App interactions, In-app search history, Installed apps, Other actions | No | — | — | — | — |
| App info and performance → Crash logs, Diagnostics, Other | No (no SDK; server logs hold no user identifiers) | — | — | — | — |
| Device or other IDs | No | — | — | — | — |
| Financial info, Contacts, Calendar, Audio, Files and docs, Web browsing | No | — | — | — | — |

**Note 1, precise location in photo EXIF.** The server strips all metadata (`storage.py`), but the
upload sent from the device may still contain GPS EXIF if the source gallery photo had it. Under
Play's definitions, data sent off the device counts as *collected*, even if the server discards it
immediately. Choose one:
- **Preferred fix:** strip EXIF on the device before upload. Re-encode the image through a canvas in
  `capturePhotoNative` (`frontend/src/lib/native.ts`) and the web upload path. Then answer **No**.
- **If you don't fix it:** declare *Precise location* as **collected, processed ephemerally,
  optional, App functionality**.

**Note 2, assistant provider.** Answering "not shared" relies on Anthropic processing the data only
on OncoAI's behalf under its commercial terms. If `ANTHROPIC_API_KEY` is unset in production, the
assistant runs entirely on the built-in knowledge base and nothing leaves OncoAI's servers. The
messages row stays the same.

---

## C. Before submitting

- [ ] `READ_MEDIA_IMAGES` / `READ_EXTERNAL_STORAGE` removed. Photo picker confirmed on Android 13+ and on an older device
- [ ] EXIF stripped on the device (or the precise-location row changed as in note 1)
- [ ] Web deletion page live
- [ ] Release API is HTTPS. `IMAGE_ENCRYPTION_KEY` set
- [ ] Merged manifest of the **release AAB** re-checked (Android Studio → Merged Manifest). Plugins can add permissions
- [ ] Answers match `01-privacy-policy.md`

---

*OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or
treatment advice.*
