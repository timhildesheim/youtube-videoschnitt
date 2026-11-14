// Misst die echten Positionen aller Einblendungen (.card/.hud/.osd + ihre Icons) im Browser-Layout 1920×1080.
//   node rects.mjs segs/<id> [segs/<id> …]   → JSON auf stdout: {id: [{id, x0, y0, x1, y1}]}
// Transformationen (Einflug-Animation) werden für die Messung neutralisiert → gemessen wird die Endposition.
import { execSync } from 'node:child_process';
import path from 'node:path';
const home = process.env.HOME;
const pp = execSync(`find ${home}/.npm/_npx -path "*node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js" | head -1`).toString().trim();
const chrome = execSync(`find ${home}/.cache/puppeteer/chrome -path "*MacOS/Google Chrome for Testing" -type f | head -1`).toString().trim();
const { default: puppeteer } = await import(pp);
const b = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--hide-scrollbars', '--allow-file-access-from-files'] });
const p = await b.newPage();
await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
const out = {};
for (const d of process.argv.slice(2)) {
  await p.goto('file://' + path.resolve(d, 'index.html'), { waitUntil: 'load', timeout: 60000 });
  await p.evaluate(() => document.fonts && document.fonts.ready);
  await new Promise(r => setTimeout(r, 300));
  out[path.basename(d)] = await p.evaluate(() => {
    const res = [];
    for (const el of document.querySelectorAll('.card[id], .hud[id], .osd[id]')) {
      const all = [el, ...el.querySelectorAll('*')];
      const keep = all.map(e => e.style.transform);
      all.forEach(e => { e.style.transform = 'none'; });
      // Eltern-Transformationen (Wrapper) ebenfalls neutralisieren
      let par = el.parentElement, pk = [];
      while (par && par !== document.body) { pk.push([par, par.style.transform]); par.style.transform = 'none'; par = par.parentElement; }
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const e of [el, ...el.querySelectorAll('img.ico')]) {
        const r = e.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) continue;
        x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom);
      }
      all.forEach((e, i) => { e.style.transform = keep[i]; });
      pk.forEach(([e, t]) => { e.style.transform = t; });
      if (x1 > x0) res.push({ id: el.id, x0: Math.round(x0), y0: Math.round(y0), x1: Math.round(x1), y1: Math.round(y1) });
    }
    return res;
  });
}
console.log(JSON.stringify(out));
await b.close();
