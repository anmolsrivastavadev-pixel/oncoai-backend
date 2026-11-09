// Generates the Android launcher icons, notification icon and splash screens
// from the original OncoAI mark. Run: npm run icons  (after `npx cap add android`)
import { mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const res = resolve(dirname(fileURLToPath(import.meta.url)), '../android/app/src/main/res');
const NAVY = '#050B1A';

const mark = (scale = 1, mono = false) => `
  <g transform="translate(32 32) scale(${scale}) translate(-32 -32)">
    <circle cx="32" cy="32" r="24" fill="none" stroke="${mono ? '#fff' : 'url(#g)'}" stroke-width="4" stroke-linecap="round" stroke-dasharray="112 39" transform="rotate(-50 32 32)"/>
    ${mono ? '' : '<circle cx="32" cy="32" r="15" fill="none" stroke="url(#g)" stroke-opacity="0.45" stroke-width="1.5"/>'}
    <circle cx="32" cy="33" r="7.5" fill="${mono ? '#fff' : 'url(#c)'}"/>
    ${mono ? '' : '<circle cx="34.5" cy="30.5" r="2.4" fill="#050B1A" fill-opacity="0.85"/>'}
    <circle cx="51" cy="15" r="3.2" fill="${mono ? '#fff' : '#2DD4BF'}"/>
  </g>`;

const defs = `<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22D3EE"/><stop offset="1" stop-color="#2DD4BF"/></linearGradient>
  <radialGradient id="c" cx="0.4" cy="0.35" r="0.7"><stop offset="0" stop-color="#67E8F9"/><stop offset="1" stop-color="#14B8A6"/></radialGradient>
  <radialGradient id="bg" cx="0.5" cy="0.4" r="0.8"><stop offset="0" stop-color="#0E2147"/><stop offset="1" stop-color="${NAVY}"/></radialGradient>
</defs>`;

const svg = (body) => Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">${defs}${body}</svg>`);

const legacy = svg(`<rect width="64" height="64" rx="14" fill="url(#bg)"/>${mark(0.72)}`);
const round = svg(`<circle cx="32" cy="32" r="32" fill="url(#bg)"/>${mark(0.66)}`);
// Adaptive foreground: content must stay inside the central 66% safe zone.
const foreground = svg(mark(0.5));
const notification = svg(mark(0.9, true));
const splash = (w, h) => {
  const s = Math.min(w, h) * 0.28;
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${defs}
      <rect width="${w}" height="${h}" fill="${NAVY}"/>
      <g transform="translate(${(w - s) / 2} ${(h - s) / 2}) scale(${s / 64})">${mark(1)}</g>
    </svg>`,
  );
};

const densities = { mdpi: 1, hdpi: 1.5, xhdpi: 2, xxhdpi: 3, xxxhdpi: 4 };
const splashSizes = {
  'port-mdpi': [320, 480], 'port-hdpi': [480, 800], 'port-xhdpi': [720, 1280], 'port-xxhdpi': [960, 1600], 'port-xxxhdpi': [1280, 1920],
  'land-mdpi': [480, 320], 'land-hdpi': [800, 480], 'land-xhdpi': [1280, 720], 'land-xxhdpi': [1600, 960], 'land-xxxhdpi': [1920, 1280],
};

const png = async (input, size, out) => {
  await mkdir(dirname(out), { recursive: true });
  await sharp(input, { density: 600 }).resize(size, size).png().toFile(out);
};

for (const [name, k] of Object.entries(densities)) {
  await png(legacy, Math.round(48 * k), `${res}/mipmap-${name}/ic_launcher.png`);
  await png(round, Math.round(48 * k), `${res}/mipmap-${name}/ic_launcher_round.png`);
  await png(foreground, Math.round(108 * k), `${res}/mipmap-${name}/ic_launcher_foreground.png`);
  await png(notification, Math.round(24 * k), `${res}/drawable-${name}/ic_stat_oncoai.png`);
}
for (const [name, [w, h]] of Object.entries(splashSizes)) {
  await sharp(splash(w, h)).png().toFile(`${res}/drawable-${name}/splash.png`);
}
await sharp(splash(480, 800)).png().toFile(`${res}/drawable/splash.png`);
console.log('Android icons and splash screens generated.');
