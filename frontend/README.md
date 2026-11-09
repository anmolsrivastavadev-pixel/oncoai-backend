# OncoAI app (React + Capacitor)

> OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.

React 18, TypeScript (strict), Tailwind CSS, Framer Motion, React Router, Recharts, and
Capacitor 6 for the Android shell. API contract: [`../docs/API_CONTRACT.md`](../docs/API_CONTRACT.md).

## Commands

```bash
npm ci
npm run dev               # web dev server on :5173 (needs the backend on VITE_API_URL)
npm run typecheck && npm run lint && npm test
npm run build             # production web build in dist/
npm run build:android     # build with .env.android, then `cap sync android`
npm run cap:open          # open the Android project in Android Studio
npm run icons             # regenerate launcher icons and splash screens
node e2e/full-flow.mjs photo.jpg   # real-browser end-to-end run (backend + `vite preview --port 5173`)
```

Android build: `cd android && ./gradlew assembleDebug`. For a release build create a
signing key, run `ONCOAI_RELEASE=1 npx cap sync android` (turns off mixed content) with
an HTTPS `VITE_API_URL`, then `./gradlew bundleRelease`.

## Structure and why

```
src/app            router (lazy-loaded pages), providers
src/components/ui  the reusable kit: Button, Card, Field, Modal/Sheet, Tabs, Toast, Skeleton...
src/components     Disclaimer (the one source of the disclaimer text), layout shell, logo
src/features/*     landing, auth, scan, tracking, care, community, assistant
src/lib            api client, token storage, native bridges, formatting, validation, safety
src/types/api.ts   types mirroring the API contract
android/           the Capacitor Android project
```

* **Feature folders** keep each phase self-contained; shared pieces live in `components/ui`.
* **One typed API client** (`lib/api.ts`) attaches the bearer token, refreshes once on a
  401 and retries, never sends the token to another origin, and normalises errors.
* **Tokens** are kept in Capacitor Preferences on the phone and `localStorage` on the web.
* **Scan photos** are never public URLs. `useAuthedImage` fetches them with the token and
  renders an object URL.
* **Native features** go through `lib/native.ts`: Capacitor Camera for capture (file input
  fallback on the web) and local notifications for reminders. Permissions are requested
  when first needed: camera, photos, notifications.
* **Safety in the UI.** The disclaimer component appears on the landing page, auth
  screens, dashboard, scan result, comparison, care and assistant. The scan result drops
  any server line containing a disease name as a second line of defence, and tests assert
  that no such word can render.
* **Fonts are bundled** (`@fontsource`) so the app works without calling a font CDN, and
  the Content Security Policy only allows connections to the configured API origin.
* **Motion** respects `prefers-reduced-motion`. Layout is mobile-first with a bottom tab
  bar and safe-area insets, and a sidebar from the `lg` breakpoint.

## Environment

| Variable | Default | Notes |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend origin. `.env.android` uses `http://10.0.2.2:8000` for the emulator. |

`screenshots/` holds the images produced by the last end-to-end run.
