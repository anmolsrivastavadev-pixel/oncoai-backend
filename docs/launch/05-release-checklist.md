# OncoAI — Google Play release checklist

> **OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.**

App ID: `com.oncoai.app` (from `frontend/capacitor.config.ts`). Stack: React + Vite + Capacitor 6.
The Android project lives in `frontend/android/` (not yet pushed when this checklist was written,
so the Gradle paths below are the Capacitor defaults).

---

## 1. Play Console account and app setup

- [ ] Developer account verified (identity and, for an organisation, a D-U-N-S number)
- [ ] **Personal accounts created after 13 Nov 2023:** before you can apply for production, you must
      run a **closed test with at least 12 testers opted in for 14 continuous days**. Plan this into
      the timeline. Internal testing does not count
- [ ] App created: name, default language, App (not Game), Free
- [ ] App content section complete: privacy policy, ads (none), app access (provide a **demo
      login** for reviewers, because every feature is behind sign-in), content rating, target audience
      (18+), news app (no), **Health apps declaration**, Data Safety, account deletion URL, government
      app (no)
- [ ] Store listing from `02-play-store-listing.md`, with screenshots that follow its rules

## 2. Signing keys

Use **Play App Signing**. Google holds the app signing key; you sign uploads with your own
**upload key**.

- [ ] Generate the upload keystore **outside the repo**:
  ```bash
  keytool -genkeypair -v \
    -keystore ~/secure/oncoai-upload.jks \
    -alias oncoai-upload \
    -keyalg RSA -keysize 4096 -validity 10000
  ```
- [ ] Store the keystore and both passwords in a password manager or secrets vault, plus one offline
      backup. **If the upload key is lost or leaked**, it can be reset through Play Console support,
      which takes days. The app signing key cannot be replaced, so let Google generate it
- [ ] Never commit the key. `.gitignore` should cover `*.jks`, `*.keystore`, `keystore.properties`.
      Add them if they're missing. This is outside `docs/`, so it's for the app agent to do
- [ ] Wire signing through an untracked `frontend/android/keystore.properties` or CI environment
      variables, never hard-coded in `build.gradle`:
  ```properties
  storeFile=/absolute/path/oncoai-upload.jks
  storePassword=…
  keyAlias=oncoai-upload
  keyPassword=…
  ```
- [ ] Enrol in Play App Signing when you upload the first AAB (the default for new apps)
- [ ] Record the **app signing key SHA-256 fingerprint** (Play Console → App integrity). You'll need
      it for any future Google API, App Links or `assetlinks.json` setup
- [ ] Optionally, a CI secret for automated uploads: a Play Developer API service account with
      release-manager permission only

## 3. Versioning

- [ ] Single source of truth: `versionName` follows semver and matches `frontend/package.json`
      `version` (currently `1.0.0`). `versionCode` is an integer that **must increase with every
      upload, on every track**. Play rejects reused codes, even from a deleted draft
- [ ] Suggested scheme: `versionCode = MAJOR*10000 + MINOR*100 + PATCH` with room for build
      numbers, for example `1.0.0` → `10000`, `1.0.1` → `10001`. Or use a CI build number
- [ ] Set in `frontend/android/app/build.gradle` → `defaultConfig { versionCode …; versionName "…" }`
- [ ] Tag each upload in git: `git tag android-v1.0.0+10000`
- [ ] **targetSdkVersion** meets Play's current requirement for new apps and updates. Check the
      *Target API level requirements* page at upload time. It was API 35 for new apps from
      31 Aug 2025, and the bar rises each year. Capacitor 6 defaults may lag behind, so check
      `frontend/android/variables.gradle`
- [ ] `minSdkVersion` as Capacitor 6 requires (22+). Consider 26+ to simplify testing

## 4. Release build configuration

- [ ] Production API: `VITE_API_URL=https://…` in an untracked `.env.production`/release env.
      **Not** `.env.android` (`http://10.0.2.2:8000` is for the emulator only)
- [ ] Build with `ONCOAI_RELEASE=1` so `allowMixedContent` is `false`:
  ```bash
  cd frontend
  ONCOAI_RELEASE=1 npm run build -- --mode production && ONCOAI_RELEASE=1 npx cap sync android
  cd android && ./gradlew bundleRelease
  # → app/build/outputs/bundle/release/app-release.aab
  ```
- [ ] Release build: `minifyEnabled true`, `shrinkResources true`, `debuggable false`. Upload the
      R8 mapping file to Play
- [ ] Network security config: cleartext traffic **disabled** for release
- [ ] Merged manifest checked. Only needed permissions: `INTERNET`, `CAMERA`, `POST_NOTIFICATIONS`.
      Use the photo picker instead of `READ_MEDIA_IMAGES`/`READ_EXTERNAL_STORAGE`. If you request
      `SCHEDULE_EXACT_ALARM`/`USE_EXACT_ALARM`, you must justify it or remove it. Reminders work with
      inexact alarms
- [ ] `android:allowBackup` reviewed. Exclude the token store from backup, or set `false`
- [ ] App icon, adaptive icon, notification icon `ic_stat_oncoai` and splash screen present
- [ ] WebView debugging disabled in release

### Backend (production)

- [ ] `ENVIRONMENT=production`, so the strong `SECRET_KEY` check is enforced
- [ ] `IMAGE_ENCRYPTION_KEY` set and backed up. Without it, stored photos can't be read
- [ ] `SEED_SAMPLE_DATA=false` (no fictional dermatologists in production, see policy review 3.5)
- [ ] `CORS_ORIGINS` limited to the app origins
- [ ] HTTPS with a valid certificate. Database and upload storage backups encrypted
- [ ] `ANTHROPIC_API_KEY` set only if the assistant is shipping and covered in the privacy policy
- [ ] Logs exclude tokens, passwords, image bytes and health notes

## 5. Internal testing track

- [ ] Play Console → Testing → **Internal testing** → create a release → upload the signed AAB
- [ ] Add testers by email list or Google Group (up to 100). Share the opt-in link
- [ ] Release notes from `02-play-store-listing.md`
- [ ] Internal builds are available within minutes and skip full review. Use this track for every
      build first
- [ ] Check the **pre-launch report** (automated device tests, crashes, accessibility, security
      warnings) and fix any blocking issues
- [ ] Smoke test on at least 3 physical devices or API levels, including the lowest supported:
  - [ ] Sign up → disclaimer consent → privacy policy link opens
  - [ ] Camera permission prompt → take photo → photo saved. No concern level or score appears
        anywhere (policy review 3.1)
  - [ ] Pick from gallery via the photo picker
  - [ ] Compare two photos
  - [ ] Reminder notification permission → reminder fires
  - [ ] Community: post, anonymous post, report, block
  - [ ] Assistant: refuses diagnosis or treatment questions. Report control works
  - [ ] **Settings → Delete account** removes everything. The user can't log back in, and the photo
        URLs return 404
  - [ ] Works offline (useful error states) and against the production HTTPS API
  - [ ] The disclaimer appears on every required screen (policy review 3.3)
- [ ] Then promote to **Closed testing** (12+ testers for 14 days, if your account needs it) →
      apply for production → staged rollout (for example 10% → 50% → 100%)

## 6. Submission gate

- [ ] Every **[Blocker]** in `04-health-policy-review.md` is resolved
- [ ] Data Safety form answered and matches the build (`03-data-safety-form.md`)
- [ ] Privacy policy and account deletion pages are live at public URLs
- [ ] Reviewer demo account works and is noted under *App access*
- [ ] versionCode is higher than any previous upload. The git tag is pushed

---

*OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or
treatment advice.*
