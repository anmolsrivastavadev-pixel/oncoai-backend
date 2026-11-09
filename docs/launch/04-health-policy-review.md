# OncoAI — Google Play health and medical device policy review

> **OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.**

*Product and policy review, not legal advice. Before submitting, get advice from a regulatory
specialist on medical device classification in each launch market (FDA, EU MDR, UK MHRA, and others).*

Sources: Google Play Policy Center, *Health Content and Services* and *Account deletion
requirements*, read on 2026-11-09. Code reviewed: branch `oncoai-platform` at `96a70bb`.

---

## 1. Summary

The UI wording is already careful. There are no disease names, the disclaimer is a single constant
used everywhere, and `scrubDiagnosticTerms` is a good defensive filter. **The problem is the scan
feature itself, not its wording.**

`backend/app/ml/concern.py` takes a skin-lesion classifier trained on HAM10000
(`Anwarkh1/Skin_Cancer-Image_Classification`). It weights that classifier's **melanoma and basal cell
carcinoma probabilities** (`DEFAULT_LABEL_WEIGHTS`) at 60%, combines the result with image features
and symptoms, and sorts each spot into a **low / moderate / higher** concern level with a 0–100 score.
A "higher" result advises seeing a dermatologist. A "low" result shows *"No prominent irregular
visual patterns detected."*

A disclaimer cannot fix this. The software analyses a photo of a lesion and tells the user how
concerned to be. That is risk stratification, and it is the textbook intended use of a regulated
medical device, called software as a medical device (SaMD). Regulators look at what the software
*does*, not at how its output is worded. Avoiding disease names does not change the intended use.
A "low" result is also the most dangerous output: a user may decide not to see a doctor because of it.

Google Play gives two routes:

| Route | What Play requires | What OncoAI must do |
|---|---|---|
| **A. Educational / wellness app (recommended for launch)** | Health apps declaration. A disclaimer in the description that the app *"is not a medical device and does not diagnose, treat, cure, or prevent any medical condition"*. A reminder to *"consult a healthcare professional"*. No misleading health functionality | **Remove graded risk output** (section 3.1) and make the other changes in section 3 |
| **B. Regulated medical device** | Declare as a medical device. Play labels the app "Medical Device". Provide proof of clearance or certification (for example FDA 510(k)/De Novo, or CE marking under EU MDR, likely class IIa or higher) on request | Clinical validation, a quality management system (ISO 13485), risk management (ISO 14971), post-market surveillance. This takes months to years. Not feasible for this release |

**Recommendation: launch on Route A.** Make the changes marked **[Blocker]** below before submitting.

## 2. What Google Play requires of a non-device health app

From the Health Content and Services policy:

1. **Health apps declaration.** Complete *App content → Health apps* in the Play Console. OncoAI
   fits categories such as *Medical / health education* and *Health tracking*, but **do not tick any
   medical device category** on Route A.
2. **Disclaimer in the store description** that the app is not a medical device and does not
   diagnose, treat, cure or prevent any medical condition. This is in the full description draft in
   `02-play-store-listing.md`.
3. **Remind users to consult a healthcare professional** for medical advice, diagnosis or treatment,
   both in the app and in the listing.
4. **No misleading or potentially harmful health functionality, and no health misinformation.**
   A reassuring "low" result from an unvalidated model is the main risk under this rule.
5. **Privacy policy:** linked in the Play Console *and* inside the app. It must be public, not
   editable and not a PDF, and fully describe how sensitive data is handled.
6. **Least permissions:** request only what core features need. Remove unused permissions.
7. **Account deletion:** an in-app deletion path *and* a web deletion link, both declared in the
   Data Safety form.

Other policies that apply:
- **User-generated content** (community). Requires: in-app reporting (exists), moderation (exists),
  a way to **block** users (missing), published content rules users accept, and timely removal of
  objectionable content.
- **AI-generated content** (assistant). Requires: users must be able to report or flag offensive AI
  output in the app, and the content must be checked against the restricted content policies.
- **Target audience and content:** set 18+. Do not target children.

## 3. Required changes

### 3.1 Scan results — **[Blocker]**

| Today (`oncoai-platform`) | Change to |
|---|---|
| `concern_level` low / moderate / higher and `concern_score` 0–100 shown to users | **Remove both from every user-facing surface** (API response, scan result, lesion cards, dashboard `concern_breakdown`, `score_trend`, compare `deltas.concern_score`). The internal score may not be used to choose which messages appear |
| Headline varies by level ("No prominent irregular visual patterns…" / "…Consider professional dermatologist evaluation.") | **One neutral headline for every scan**, for example "Photo saved to your skin journal." No reassuring wording, ever |
| Dermatologist advice appears only when the result is "higher" | **The same advice on every scan, whatever the analysis says**: "Only a healthcare professional can assess a skin spot. If you notice changes, bleeding, or anything that worries you, contact a doctor or dermatologist." |
| Symptom bumps raise the concern score | Symptoms are **logged and shown** to the user. Educational rule: if the user ticks bleeding or a change in size, shape or colour, always show "These are changes worth showing a doctor", based only on what the user ticked, not on any model output |
| Classifier trained on disease classes (HAM10000 melanoma/BCC weights) drives the result | **Do not use the disease classifier in the user-facing product.** Keep only descriptive computer-vision measurements (symmetry, border, colour variety, relative size) and photo-quality checks. Present them as descriptions ("the two halves look different in shape"), not as a judgement, and say they come from the photo, not from a medical assessment |
| Feature values shown as 0–100 bars with colour coding | Neutral display without red/amber/green and without "good"/"bad" thresholds. In comparisons, show "changed / similar", not "worse / better" |

Also check:
- The HAM10000 dataset is licensed **CC BY-NC 4.0 (non-commercial)**. Check the model's licence and
  your monetisation plans before shipping the weights, even internally.
- `/health` returns `model.kind`, and `Scan.model` returns the model's name and version. That's fine
  internally, but don't show "AI model" credentials to users as if they were a clinical credential.

### 3.2 Wording — **[Blocker]**

Use the wording on the left. Don't use the wording on the right.

| ✅ Use | ❌ Avoid |
|---|---|
| skin journal, photo log, track, notice changes | scan result, analysis result, assessment, check-up |
| visual features, described, looks | detect, detected, identify, screen, screening |
| learn, awareness, guide, ABCDE rule (educational) | risk, risk level, concern level, score, likelihood |
| "talk to a doctor or dermatologist" | "you should get this checked" only when the model says so |
| "OncoAI cannot tell whether a spot is harmful" | "no concerns found", "looks normal", "low risk", "all clear" |
| educational assistant | AI dermatologist, AI doctor, second opinion |

- **The word "Scan" itself:** rename the Scans tab and `POST /scans` UI copy to "Add photo" or
  "Journal entry". The API path can stay.
- `HEADLINES` and `POOR_QUALITY_HEADLINE` in `concern.py` use "detected" and "reliable visual check".
  Replace them. ("Retake the photo in good light" is fine.)
- Add these to `FORBIDDEN_DIAGNOSTIC_TERMS` in tests: `risk`, `concern level`, `screening`,
  `detected`, `normal`, `all clear`, `low risk`, `high risk`.

### 3.3 Disclaimer placement — **[Blocker]**

Show the exact string, *"OncoAI is an educational skin health awareness platform and does not
provide medical diagnosis or treatment advice."*, together with the Play wording, *"OncoAI is not a
medical device and does not diagnose, treat, cure, or prevent any medical condition. Consult a
healthcare professional for medical advice, diagnosis, or treatment."*:

- [ ] onboarding (a full-screen step, with a checkbox the user must tick: *"I understand OncoAI is
      educational and is not a substitute for a doctor"*). Store the acceptance with a timestamp
- [ ] before the first photo upload (explicit consent to process skin photos and health data,
      separate from accepting the terms)
- [ ] on every photo entry screen and the compare screen (`Disclaimer variant="banner"`)
- [ ] in every assistant reply (the API already includes it)
- [ ] Settings → About
- [ ] store listing description and screenshots

### 3.4 Assistant — **[Blocker]**

At `55d1bac` the assistant has input and output guardrails and a knowledge-base fallback, and it
doesn't store chats. That's good. Two things must change along with 3.1:
`claude_provider.SYSTEM_PROMPT` tells the model to explain "the app's educational concern levels
(low / moderate / higher)". `service.scan_context_text` also sends the concern level and score.
Remove both when concern levels are removed.

The API contract's guardrails are a good start: no diagnosis, no treatment, urgent symptoms are
redirected, self-harm leads to crisis resources. Also add:
- When `context.scan_id` is attached, the assistant must not interpret the scan's meaning
  ("this could be…", "this looks fine"). It may only explain what the descriptive features mean
  in general terms.
- Refuse requests to rank, compare against disease images, or estimate likelihood.
- No medication, dosage, home-remedy or "wait and see" advice.
- A **report this reply** control on every AI message (Play AI-generated content policy).
- Show crisis lines for the user's region, with a generic fallback.
- Log `safety.redirected` events for review.

### 3.5 Dermatologist directory and booking — **[Blocker]**

- Seed data are **fictional sample listings** (`is_sample: true`, `SEED_SAMPLE_DATA=True` by
  default). Showing fictional doctors with ratings and bookable slots in a public release is
  misleading. Either:
  - **turn this off in production** (`SEED_SAMPLE_DATA=false`) and hide the feature until you have
    real, verified listings and a real booking integration; **or**
  - replace it with links to official "find a dermatologist" directories (for example national
    dermatology associations).
- If you add real listings later, don't show ratings unless they come from a source you're allowed
  to use. Say clearly that OncoAI does not endorse providers.
- A "booked" appointment that is never sent to a clinic is misleading. Call it "Planned
  appointment (add to your own calendar)", or integrate a real booking system.

### 3.6 Community — required before launch

- [ ] Block or mute users (Play UGC requirement)
- [ ] Content rules shown and accepted before a user's first post
- [ ] Moderators respond within a set time, for example 24 h for reports
- [ ] A pinned notice: "Community posts are personal experiences, not medical advice"
- [ ] Filter posts that diagnose others ("that's definitely melanoma") or recommend treatments
- [ ] Anonymous posts still linked internally (as the privacy policy states)

### 3.7 Branding

- "OncoAI" includes *onco-* (cancer). Keep the title's descriptive part about education
  (for example "OncoAI: Skin Health Journal"), and never pair the name with "cancer",
  "detection" or "screening" in the listing, screenshots or onboarding.
- Category: **Health & Fitness**, not *Medical*.

### 3.8 Privacy and data — required

- [ ] Privacy policy at a public HTML URL, linked on the sign-up screen and in Settings
- [x] In-app **Profile → Delete account** using `DELETE /users/me` (present at `55d1bac`). Check
      that the confirmation lists what will be deleted
- [ ] Remove `READ_MEDIA_IMAGES` / `READ_EXTERNAL_STORAGE` from the manifest and use the system photo
      picker (Play photo and video permissions policy)
- [ ] Strip EXIF on the device before upload (see `03-data-safety-form.md` note 1)
- [ ] A public web deletion page that names "OncoAI"
- [ ] `IMAGE_ENCRYPTION_KEY` **required** when `ENVIRONMENT=production` (today it's optional).
      Treat a missing key as a release blocker in deployment config
- [ ] Production API on HTTPS only. Release build without `allowMixedContent`
- [ ] Data Safety form completed once the code is final (see `03-data-safety-form.md`)

## 4. Pre-submission compliance checklist

- [ ] No user-visible concern level, score, risk wording or level-dependent advice (3.1)
- [ ] Disease classifier not used for any user-facing output (3.1)
- [ ] Banned words removed from app, API strings, listing and screenshots (3.2; listing rules in 02)
- [ ] Disclaimer and Play wording present in every required place (3.3)
- [ ] Assistant guardrails and report control in place (3.4)
- [ ] Fictional dermatologist listings turned off or replaced (3.5)
- [ ] Community block, rules and moderation in place (3.6)
- [ ] Health apps declaration: no medical device category ticked
- [ ] Privacy policy, in-app deletion and web deletion live (3.8)
- [ ] Data Safety form matches the build
- [ ] Regulatory specialist confirms the final feature set is outside device regulation in the
      launch markets
- [ ] Content rating questionnaire answered, including user-generated content and user interaction

---

*OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or
treatment advice.*
