/* global localStorage */
// Second E2E pass for flows not covered by full-flow.mjs: scan comparison, reminders,
// and moderation. Seeds data through the real API, then drives the real UI.
//   node e2e/extras.mjs <imageA.jpg> <imageB.jpg> <moderatorEmail> <moderatorPassword>
// The moderator account must already exist (backend/scripts/create_admin.py).
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const APP = process.env.APP_URL ?? 'http://localhost:5173';
const API = (process.env.API_URL ?? 'http://localhost:8000') + '/api/v1';
const [imgA, imgB, modEmail, modPassword] = process.argv.slice(2);
const SHOTS = new URL('../screenshots/', import.meta.url).pathname;

const call = async (path, { token, json, form, method } = {}) => {
  const r = await fetch(API + path, {
    method: method ?? (json || form ? 'POST' : 'GET'),
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(json ? { 'Content-Type': 'application/json' } : {}) },
    body: json ? JSON.stringify(json) : form,
  });
  if (!r.ok) throw new Error(`${path} -> ${r.status} ${await r.text()}`);
  return r.status === 204 ? null : r.json();
};
const upload = (token, file, lesionId) => {
  const f = new FormData();
  f.append('image', new Blob([readFileSync(file)], { type: 'image/jpeg' }), 'spot.jpg');
  if (lesionId) f.append('lesion_id', String(lesionId));
  return call('/scans', { token, form: f });
};

const email = `extras_${Date.now()}@example.com`;
const user = await call('/auth/register', { json: { email, password: 'Sunny-day42', full_name: 'Noor Tester' } });
const s1 = await upload(user.access_token, imgA);
const s2 = await upload(user.access_token, imgB, s1.lesion_id);
const post = await call('/community/posts', { token: user.access_token, json: { title: 'Reported example post', body: 'Body of a post that gets reported.', topic: 'questions' } });
const other = await call('/auth/register', { json: { email: `r_${email}`, password: 'Sunny-day42', full_name: 'Rae Reporter' } });
await call(`/community/posts/${post.id}/report`, { token: other.access_token, json: { reason: 'Testing the moderation queue' } });
const mod = await call('/auth/login', { json: { email: modEmail, password: modPassword } });

const browser = await chromium.launch();
const open = async (tokens) => {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await ctx.addInitScript((t) => {
    localStorage.setItem('oncoai.access_token', t.access_token);
    localStorage.setItem('oncoai.refresh_token', t.refresh_token);
  }, tokens);
  return ctx.newPage();
};
const shot = async (page, name) => {
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${SHOTS}mobile-extra-${name}.png`, fullPage: true });
};

let page = await open(user);
await page.goto(`${APP}/tracking/compare?a=${s1.id}&b=${s2.id}`);
await page.getByText(/concern score/i).first().waitFor();
await page.getByText('OncoAI is an educational skin health awareness platform').first().waitFor();
await shot(page, 'compare');
console.log('ok   compare');

await page.goto(`${APP}/track/${s1.lesion_id}`);
await page.getByText('Scan timeline').waitFor();
await shot(page, 'timeline-two-scans');
console.log('ok   timeline');

await page.goto(`${APP}/care`);
await page.getByRole('tab', { name: 'Reminders' }).or(page.getByRole('button', { name: 'Reminders' })).first().click();
await page.getByRole('button', { name: /add|new/i }).first().click();
await page.getByLabel('Title').fill('Monthly skin self-check');
await page.locator('[role=dialog] button').filter({ hasText: /save|add|create/i }).last().click();
await page.getByText('Monthly skin self-check').first().waitFor();
await shot(page, 'reminders');
console.log('ok   reminders');

await page.goto(`${APP}/moderation`);
await page.waitForURL((u) => !u.pathname.startsWith('/moderation'), { timeout: 5000 }).catch(() => {});
if (new URL(page.url()).pathname.startsWith('/moderation') && (await page.getByText('Testing the moderation queue').count())) throw new Error('regular user can see the moderation queue');
console.log('ok   moderation hidden from regular users');

page = await open(mod);
await page.goto(`${APP}/moderation`);
await page.getByText('Testing the moderation queue').first().waitFor();
await shot(page, 'moderation');
await page.getByRole('button', { name: /remove/i }).first().click();
await page.waitForTimeout(1200);
const after = await call(`/community/posts?limit=50`, { token: user.access_token });
if (after.items.some((p) => p.id === post.id)) throw new Error('removed post is still in the feed');
console.log('ok   moderation remove_content');
await browser.close();
console.log('ALL EXTRA STEPS PASSED');
