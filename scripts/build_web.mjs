// Convierte data/*.csv + config/exchange_rate.json a site/data/data.json (sin dependencias).
import fs from 'node:fs'; import path from 'node:path';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const parse = (txt) => { const [h, ...rows] = txt.trim().split(/\r?\n/).map(l => l.split(','));
  return rows.map(r => Object.fromEntries(h.map((k, i) => [k, r[i] !== '' && !isNaN(r[i]) && !['mes','sku','cliente_id','centro_costo_id'].includes(k) ? +r[i] : r[i]]))); };
const out = { generado: new Date().toISOString(), fx: JSON.parse(fs.readFileSync(path.join(root, 'config/exchange_rate.json'))) };
for (const f of fs.readdirSync(path.join(root, 'data')).filter(f => f.endsWith('.csv')))
  out[f.replace('.csv', '')] = parse(fs.readFileSync(path.join(root, 'data', f), 'utf8')).map(r => { delete r.empresa; for (const k of Object.keys(r)) if (k.endsWith('_usd')) delete r[k]; return r; });
out.empresa = 'NovaCampo Alimentos S.A.';
fs.mkdirSync(path.join(root, 'site/data'), { recursive: true });
fs.writeFileSync(path.join(root, 'site/data/data.json'), JSON.stringify(out));
console.log('site/data/data.json OK —', Object.keys(out).length, 'claves');
