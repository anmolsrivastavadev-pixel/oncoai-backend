# OncoAI API Contract (v1)

Single source of truth between `backend/` (FastAPI) and `frontend/` (React + Capacitor).
Base URL: `${VITE_API_URL}` (default `http://localhost:8000`), all routes under `/api/v1`.
All JSON. Timestamps are ISO-8601 UTC strings. IDs are integers.

## Conventions
- Auth: `Authorization: Bearer <access_token>` (JWT HS256, `sub` = user id, `type` = "access", exp 30 min).
  Refresh token (JWT, `type` = "refresh", exp 14 days) exchanged at `/auth/refresh`.
- Errors: `{"detail": "<message>"}` (FastAPI default), 401 for missing/invalid token, 403 forbidden, 404 not found, 422 validation, 429 rate limit.
- Pagination: `?limit=20&offset=0` → response `{"items": [...], "total": N}`.
- Every scan/assistant response carries `"disclaimer"`: the exact string
  `OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.`

## Health
- `GET /health` → `{"status":"ok","db":"ok","model":{"loaded":bool,"name":str,"kind":"vit"|"heuristic"}}`

## Auth  (`/api/v1/auth`)
- `POST /register` `{email, password (min 8, ≥1 letter & ≥1 digit), full_name}` → 201 `TokenPair`
- `POST /login` `{email, password}` → `TokenPair` (401 on bad creds; 5 attempts/min/IP rate limit)
- `POST /refresh` `{refresh_token}` → `TokenPair`
- `TokenPair` = `{access_token, refresh_token, token_type:"bearer", user: User}`

## Users (`/api/v1/users`)
- `GET /me` → `User`
- `PATCH /me` `{full_name?, date_of_birth? (YYYY-MM-DD), skin_type? (I–VI fitzpatrick string "I".."VI"), location?, bio?}` → `User`
- `POST /me/password` `{current_password, new_password}` → 204
- `DELETE /me` → 204 (deletes user and all their data + images)
- `User` = `{id, email, full_name, date_of_birth, skin_type, location, bio, role:"user"|"moderator"|"admin", created_at}`

## Lesions (`/api/v1/lesions`) — a tracked spot on the body
- `GET /` → `{"items":[Lesion], "total"}`
- `POST /` `{label, body_location, notes?}` → 201 `Lesion`
- `GET /{id}` → `Lesion` with `scans: [ScanSummary]` (newest first)
- `PATCH /{id}` `{label?, body_location?, notes?}` → `Lesion`
- `DELETE /{id}` → 204
- `Lesion` = `{id, label, body_location, notes, created_at, scan_count, latest_concern: ConcernLevel|null, latest_scan_at|null, thumbnail_url|null}`
- body_location values: `head_neck, face, scalp, chest, abdomen, back, upper_arm_left, upper_arm_right, forearm_left, forearm_right, hand_left, hand_right, thigh_left, thigh_right, lower_leg_left, lower_leg_right, foot_left, foot_right, other`

## Scans (`/api/v1/scans`)
- `POST /` multipart: `image` (jpeg/png/webp, ≤10 MB), `lesion_id?` (int), `symptoms?` (JSON string of `Symptoms`) → 201 `Scan`
  - If no `lesion_id`, server creates a lesion labelled "Spot <n>" at `other`.
- `GET /?lesion_id=&limit=&offset=` → `{"items":[ScanSummary], "total"}`
- `GET /{id}` → `Scan`
- `DELETE /{id}` → 204
- `GET /{id}/image` → image bytes (auth required; owner only). Frontend fetches with Authorization header and renders via object URL.
  `?variant=thumb` returns 256px thumbnail.
- `ConcernLevel` = `"low" | "moderate" | "higher"`
- `Symptoms` = `{itching: bool, bleeding: bool, pain: bool, changed_size: bool, changed_color: bool, changed_shape: bool, new_spot: bool, notes?: str}`
- `ScanSummary` = `{id, lesion_id, created_at, concern_level, concern_score (0-100), thumbnail_url, headline}`
- `Scan` = ScanSummary + `{
    image_url,
    quality: {ok: bool, blur_score, brightness, contrast, issues: [str]},
    features: {asymmetry: 0-100, border_irregularity: 0-100, color_variation: 0-100, diameter_px, diameter_relative: 0-100 (share of frame), color_count:int},
    observations: [str],           // e.g. "Irregular visual patterns detected."
    recommendations: [str],        // e.g. "Consider professional dermatologist evaluation."
    symptoms: Symptoms|null,
    model: {name, kind:"vit"|"heuristic", version},
    disclaimer
  }`
  - The API NEVER returns disease/class names. Model class probabilities stay internal.
  - `headline` examples: low → "No prominent irregular visual patterns detected.", moderate → "Some irregular visual patterns detected.", higher → "Irregular visual patterns detected. Consider professional dermatologist evaluation."

## Comparison & analytics (`/api/v1/tracking`)
- `GET /compare?a=<scan_id>&b=<scan_id>` → `{a: Scan, b: Scan, deltas: {asymmetry, border_irregularity, color_variation, diameter_relative, concern_score}, summary: str}` (both scans must belong to the user)
- `GET /dashboard` → `{
    totals: {lesions, scans, upcoming_appointments},
    concern_breakdown: {low:int, moderate:int, higher:int},   // by latest scan per lesion
    scans_over_time: [{date:"YYYY-MM-DD", count:int}],          // last 90 days
    score_trend: [{date, lesion_id, lesion_label, concern_score}],
    recent_scans: [ScanSummary] (5),
    next_appointment: Appointment|null,
    reminders: [Reminder] (due/upcoming 5)
  }`
- `GET /symptoms` → `{"items":[SymptomLog]}` ; `POST /symptoms` `{lesion_id?, ...Symptoms}` → 201 `SymptomLog`
- `SymptomLog` = `{id, lesion_id|null, created_at, ...Symptoms}`

## Dermatologists & appointments
- `GET /api/v1/dermatologists?q=&city=&specialty=&limit=&offset=` → `{"items":[Dermatologist], "total"}`
- `GET /api/v1/dermatologists/{id}` → `Dermatologist`
- `GET /api/v1/dermatologists/{id}/availability?date=YYYY-MM-DD` → `{"date", "slots": ["09:00","09:30",...]}` (30 min slots 09:00–17:00 Mon–Fri, minus booked; empty on weekends / past)
- `Dermatologist` = `{id, name, title, specialty, clinic_name, city, address, phone, rating, review_count, languages:[str], accepts_new_patients, bio, is_sample: bool}`
  - Seed data are clearly fictional sample listings (`is_sample: true`); UI shows a "Sample listing" badge.
- `GET /api/v1/appointments?status=upcoming|past|all` → `{"items":[Appointment], "total"}`
- `POST /api/v1/appointments` `{dermatologist_id, date:"YYYY-MM-DD", time:"HH:MM", reason, scan_id?}` → 201 `Appointment` (409 if slot taken)
- `PATCH /api/v1/appointments/{id}` `{date?, time?, reason?}` → `Appointment` (reschedule)
- `POST /api/v1/appointments/{id}/cancel` → `Appointment`
- `Appointment` = `{id, dermatologist: Dermatologist, scheduled_at, reason, status:"booked"|"cancelled"|"completed", scan_id|null, created_at}`

## Reminders (`/api/v1/reminders`)
- `GET /` → `{"items":[Reminder]}` ; `POST /` `{title, kind:"rescan"|"appointment"|"self_check"|"custom", due_at, lesion_id?, appointment_id?, repeat_days?:int}` → 201
- `PATCH /{id}` `{title?, due_at?, done?}` ; `DELETE /{id}` → 204
- Booking an appointment auto-creates a reminder 24 h before.
- `Reminder` = `{id, title, kind, due_at, done, lesion_id|null, appointment_id|null, repeat_days|null}`

## Community (`/api/v1/community`)
- `GET /posts?topic=&limit=&offset=` → `{"items":[Post], "total"}`
- `POST /posts` `{title (3-150), body (1-5000), topic:"support"|"awareness"|"prevention"|"stories"|"questions", anonymous?:bool}` → 201 `Post`
- `GET /posts/{id}` → Post with `comments: [Comment]`
- `DELETE /posts/{id}` → 204 (author or moderator)
- `POST /posts/{id}/comments` `{body (1-2000), anonymous?}` → 201 `Comment`; `DELETE /comments/{id}` → 204
- `POST /posts/{id}/reactions` `{kind:"support"|"hug"|"strength"|"relate"}` → toggles; returns `{reactions: {support:n,...}, my_reactions:[kind]}`
- `POST /posts/{id}/report` / `POST /comments/{id}/report` `{reason}` → 201 `{id, status:"open"}`
- Moderation (role moderator/admin): `GET /moderation/reports?status=open` ; `POST /moderation/reports/{id}/resolve` `{action:"dismiss"|"remove_content"}`
- `Post` = `{id, title, body, topic, author: {id|null, display_name}, created_at, comment_count, reactions:{support,hug,strength,relate}, my_reactions:[kind], is_mine, status:"visible"|"removed"}`
- `Comment` = `{id, post_id, body, author:{id|null, display_name}, created_at, is_mine}`
- Server-side content filter: posts/comments containing phone numbers/emails are rejected (422) to protect privacy; profanity masked; posts with >=3 open reports auto-hidden pending review.

## Assistant (`/api/v1/assistant`)
- `POST /chat` `{messages: [{role:"user"|"assistant", content}], context?: {scan_id?}}` → `{reply, sources:[{title, url}], suggestions:[str], provider:"claude"|"knowledge_base", disclaimer, safety: {redirected: bool, reason|null}}`
- `GET /topics` → `{"items":[{id, title, summary}]}` (educational articles: ABCDE rule, UV protection, self-exam how-to, what a dermatologist visit involves, understanding your scan result, skin types)
- Guardrails: never diagnose, never recommend treatment/medication, never claim to replace doctors; urgent symptoms (rapid bleeding, etc.) → advise contacting a healthcare professional; self-harm → crisis resources.
