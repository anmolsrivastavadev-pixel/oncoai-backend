/* global document */
// End-to-end smoke test against a REAL backend (no mocks).
//   backend on :8000, `vite preview --port 5173`, then: node e2e/full-flow.mjs <image.jpg>
// Takes screenshots into ./screenshots and exits non-zero on the first failed step.
import { createRequire } from 'node:module';
import { mkdirSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const APP = process.env.APP_URL ?? 'http://localhost:5173';
const IMAGE = process.argv[2];
const SHOTS = new URL('../screenshots/', import.meta.url).pathname;
const DISCLAIMER = 'OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.';
const FORBIDDEN = /melanoma|carcinoma|malignan|benign|keratos|nevus|naevus|you have cancer/i;
mkdirSync(SHOTS, { recursive: true });

const mobile = process.env.VIEWPORT !== 'desktop';
const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: mobile ? { width: 390, height: 844 } : { width: 1280, height: 800 },
  deviceScaleFactor: 2,
  isMobile: mobile,
  hasTouch: mobile,
});
const page = await ctx.newPage();
const tag = mobile ? 'mobile' : 'desktop';
const errors = [];
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('console', (m) => m.type() === 'error' && errors.push(`console: ${m.text()}`));
page.on('response', (r) => r.status() >= 500 && errors.push(`HTTP ${r.status()} ${r.url()}`));

let n = 0;
const shot = async (name) => {
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${SHOTS}${tag}-${String(++n).padStart(2, '0')}-${name}.png` });
};
const step = async (name, fn) => {
  try {
    await fn();
    console.log(`ok   ${name}`);
  } catch (e) {
    await page.screenshot({ path: `${SHOTS}${tag}-FAIL-${name.replace(/\W+/g, '-')}.png` }).catch(() => {});
    console.error(`FAIL ${name}\n${e.message}`);
    console.error(errors.join('\n'));
    await browser.close();
    process.exit(1);
  }
};
const expectDisclaimer = async () => {
  await page.getByText(DISCLAIMER).first().waitFor({ timeout: 8000 });
};
const noOverflow = async (name) => {
  const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  if (over > 1) throw new Error(`${name}: horizontal overflow of ${over}px`);
};

const email = `e2e_${Date.now()}@example.com`;

await step('landing page', async () => {
  await page.goto(APP);
  await page.getByText('Scan. Track. Stay Informed.').first().waitFor();
  await expectDisclaimer();
  await noOverflow('landing');
  await shot('landing');
  await page.screenshot({ path: `${SHOTS}${tag}-landing-full.png`, fullPage: true });
});

await step('protected route redirects to login', async () => {
  await page.goto(`${APP}/dashboard`);
  await page.waitForURL(/\/login/);
  await expectDisclaimer();
  await shot('login');
});

await step('signup', async () => {
  await page.goto(`${APP}/signup`);
  await page.getByLabel('Full name').fill('Eva Tester');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password', { exact: true }).fill('Sunny-day42');
  await page.getByLabel('Confirm password').fill('Sunny-day42');
  await page.getByRole('checkbox').check();
  await shot('signup');
  await page.locator('button[type=submit]').click();
  await page.waitForURL(/\/dashboard/);
  await expectDisclaimer();
  await shot('dashboard-empty');
});

let scanUrl;
await step('scan: new spot, photo, analyse, result', async () => {
  await page.goto(`${APP}/scan`);
  await page.getByLabel('Spot name').fill('Mole on left shoulder');
  await page.getByRole('radio', { name: 'Upper arm (left)' }).or(page.getByRole('button', { name: 'Upper arm (left)' })).first().click();
  await shot('scan-spot');
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.getByTestId('file-input').setInputFiles(IMAGE);
  await shot('scan-preview');
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.getByText("Anything you've noticed?").waitFor();
  await shot('scan-symptoms');
  await page.getByRole('button', { name: /analy/i }).click();
  await page.getByTestId('scan-result').waitFor({ timeout: 30000 });
  await expectDisclaimer();
  const text = await page.getByTestId('scan-result').innerText();
  if (!/(low|moderate|higher) concern/i.test(text)) throw new Error('no concern level shown');
  if (FORBIDDEN.test(text)) throw new Error(`diagnostic term shown: ${text.match(FORBIDDEN)[0]}`);
  await noOverflow('scan result');
  scanUrl = page.url();
  await shot('scan-result');
  await page.screenshot({ path: `${SHOTS}${tag}-scan-result-full.png`, fullPage: true });
});

await step('dashboard shows the scan', async () => {
  await page.goto(`${APP}/dashboard`);
  await page.getByText('Concern breakdown').waitFor();
  await page.getByText(/higher concern|moderate concern|low concern/i).first().waitFor();
  await noOverflow('dashboard');
  await shot('dashboard');
  await page.screenshot({ path: `${SHOTS}${tag}-dashboard-full.png`, fullPage: true });
});

await step('tracking: lesion timeline', async () => {
  await page.goto(`${APP}/track`);
  await page.getByText('Mole on left shoulder').first().click();
  await page.waitForURL(/\/track\/\d+/);
  await page.waitForLoadState('networkidle');
  await noOverflow('lesion detail');
  await shot('lesion-detail');
});

await step('care: search and book a dermatologist', async () => {
  await page.goto(`${APP}/care`);
  await page.getByText(/sample listing/i).first().waitFor();
  await expectDisclaimer();
  await shot('care-search');
  await page.getByRole('button', { name: /^Dr\./ }).first().click();
  await page.getByRole('radiogroup', { name: 'Time' }).waitFor({ timeout: 15000 }).catch(async () => {
    // today may be a weekend / fully past: pick later dates until slots appear
    const days = page.getByRole('radiogroup', { name: 'Date' }).getByRole('radio');
    for (let i = 1; i < 6; i++) {
      await days.nth(i).click();
      if (await page.getByRole('radiogroup', { name: 'Time' }).isVisible().catch(() => false)) break;
      await page.waitForTimeout(600);
    }
  });
  await page.getByRole('radiogroup', { name: 'Time' }).getByRole('radio').first().click();
  await page.getByLabel('Reason for visit').fill('A spot on my shoulder looks different from the others.');
  await shot('care-booking');
  await page.getByRole('button', { name: /^Book / }).click();
  await page.getByRole('button', { name: 'Done' }).waitFor();
  await shot('care-booked');
});

await step('community: create a post and react', async () => {
  await page.goto(`${APP}/community`);
  await shot('community');
  await page.getByRole('button', { name: /^post$|new post/i }).first().click();
  await page.getByLabel('Title').fill('Booked my first skin check');
  await page.getByLabel('Your post').fill('Feeling a bit nervous, but glad I made the appointment. Any tips for the visit?');
  await shot('community-compose');
  await page.locator('[role=dialog] button[type=submit], [role=dialog] button:has-text("Post")').last().click();
  await page.getByText('Booked my first skin check').first().waitFor();
  await noOverflow('community');
  await shot('community-posted');
});

await step('community: privacy filter rejects contact details', async () => {
  await page.getByRole('button', { name: /^post$|new post/i }).first().click();
  await page.getByLabel('Title').fill('Contact me');
  await page.getByLabel('Your post').fill('Email me at someone@example.com please');
  await page.locator('[role=dialog] button[type=submit], [role=dialog] button:has-text("Post")').last().click();
  await page.getByText(/email|phone|contact|personal/i).last().waitFor();
  await shot('community-privacy');
});

await step('assistant: educational answer and diagnosis refusal', async () => {
  await page.goto(`${APP}/assistant`);
  await expectDisclaimer();
  const box = page.getByPlaceholder('Ask a question…');
  await box.fill('What is the ABCDE rule?');
  await page.getByRole('button', { name: 'Send message' }).click();
  await page.getByText(/asymmetry/i).first().waitFor({ timeout: 20000 });
  await box.fill('Do I have skin cancer? Is my mole melanoma?');
  await page.getByRole('button', { name: 'Send message' }).click();
  await page.getByText(/can(no|')t (diagnose|tell)|not able to diagnose|unable to diagnose|cannot diagnose/i).first().waitFor({ timeout: 20000 });
  await shot('assistant');
});

await step('profile and logout', async () => {
  await page.goto(`${APP}/profile`);
  await page.getByText(email).first().waitFor();
  await shot('profile');
});

await step('scan image is not reachable without a token', async () => {
  const id = scanUrl.match(/scan\/(\d+)/)[1];
  const api = process.env.API_URL ?? 'http://localhost:8000';
  const r = await fetch(`${api}/api/v1/scans/${id}/image`);
  if (r.status !== 401) throw new Error(`expected 401, got ${r.status}`);
});

await browser.close();
const real = errors.filter((e) => !/401|422|favicon/.test(e));
if (real.length) {
  console.error('Browser errors:\n' + real.join('\n'));
  process.exit(1);
}
console.log('ALL STEPS PASSED');
