// Screenshots von Webseiten für Einblendungen (Skool-Community, Landingpages, erwähnte Tools).
//   node shots.mjs <url> <name> [--full]
// Ergebnis: assets/<name>.jpg (1440 CSS-px breit, DPR 2 → 2880 px), bei --full die ganze Seite (max. 5400 px hoch).
// Cookie-Banner: es wird nur "Nur notwendige"/"Ablehnen" geklickt (datensparsame Wahl).
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [url, name, flag] = process.argv.slice(2);
const home = process.env.HOME;
const pp = execSync(`find ${home}/.npm/_npx -path "*node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js" | head -1`).toString().trim();
const chrome = execSync(`find ${home}/.cache/puppeteer/chrome -path "*MacOS/Google Chrome for Testing" -type f | head -1`).toString().trim();
if (!pp || !chrome) { console.error('puppeteer/Chrome nicht gefunden – einmal `npx hyperframes doctor` ausführen'); process.exit(1); }
const { default: puppeteer } = await import(pp);
const b = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--hide-scrollbars'] });
const p = await b.newPage();
await p.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });
await p.goto(url, { waitUntil: 'networkidle2', timeout: 90000 });
await new Promise(r => setTimeout(r, 2500));
await p.evaluate(() => {
  for (const el of document.querySelectorAll('button,a')) {
    if (/^(nur notwendige|ablehnen|reject all|alle ablehnen)$/i.test(el.textContent.trim())) { el.click(); break; }
  }
  document.querySelectorAll('[class*="toast"],[class*="cookie"],[id*="cookie"]').forEach(e => e.remove());
});
await new Promise(r => setTimeout(r, 1200));
fs.mkdirSync('assets', { recursive: true });
const png = path.join('assets', `${name}.png`);
if (flag === '--full') {
  const h = await p.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < Math.min(h, 9000); y += 600) { await p.evaluate(y => window.scrollTo(0, y), y); await new Promise(r => setTimeout(r, 250)); }
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.setViewport({ width: 1440, height: Math.min(h, 5400), deviceScaleFactor: 2 });
  await new Promise(r => setTimeout(r, 1500));
}
await p.screenshot({ path: png });
await b.close();
execSync(`ffmpeg -v error -y -i "${png}" -q:v 2 "assets/${name}.jpg" && rm "${png}"`);
console.log(`assets/${name}.jpg`);
