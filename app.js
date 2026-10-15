'use strict';
const S = { tab: 'financiero', from: null, to: null, ccy: 'ARS', theme: localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'), producto: '', region: '', canal: '', centro: '', sku: '' };
let D, MONTHS = [], charts = [];
const $ = (s, el = document) => el.querySelector(s);
const MES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const mLabel = m => `${MES[+m.slice(5) - 1]} ${m.slice(2, 4)}`;
const conv = v => S.ccy === 'USD' ? v / D.fx.ars_per_usd : v;
// Convención AR: MM = millones, mil M = miles de millones. Toda cifra lleva ARS o USD.
const nf = (v, d) => v.toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d });
const fmt = (v, c = true) => { v = conv(v); const a = Math.abs(v);
  const s = a >= 1e9 ? nf(v / 1e9, 2) + ' mil M' : a >= 1e6 ? nf(v / 1e6, 1) + ' MM' : a >= 1e4 ? nf(v / 1e3, 1) + ' k' : nf(v, a < 100 ? 2 : 0);
  return (c ? S.ccy + ' ' : '') + s; };
const full = v => S.ccy + ' ' + conv(v).toLocaleString('es-AR', { maximumFractionDigits: S.ccy === 'USD' ? 2 : 0 });
const pct = (v, d = 1) => isFinite(v) ? (v * 100).toFixed(d).replace('.', ',') + '%' : '—';
const num = v => Math.round(v).toLocaleString('es-AR');
const sum = (a, k) => a.reduce((s, r) => s + (+r[k] || 0), 0);
const inRange = r => r.mes >= S.from && r.mes <= S.to;
const rng = k => D[k].filter(inRange);
const months = () => MONTHS.filter(m => m >= S.from && m <= S.to);
const shift = (m, n) => { const d = new Date(+m.slice(0, 4), +m.slice(5) - 1 + n, 1); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'); };
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const PAL = ['#1f6feb', '#16a34a', '#f59e0b', '#db2777', '#7c3aed', '#0891b2', '#ea580c', '#64748b'];

function toast(t) { const e = $('#tip'); e.textContent = t; e.classList.add('show'); setTimeout(() => e.classList.remove('show'), 1800); }

// ---------- KPI con deltas MoM / YoY (último mes del rango) ----------
function delta(cur, prev, invert) { if (prev == null || !isFinite(cur / prev) || prev === 0) return '<span class="mut">—</span>';
  const d = (cur - prev) / Math.abs(prev), good = invert ? d < 0 : d > 0;
  return `<span class="${good ? 'up' : 'down'}">${d >= 0 ? '▲' : '▼'} ${pct(Math.abs(d))}</span>`; }
function kpi(label, value, series, key, opts = {}) {
  const by = m => { const rs = series.filter(r => r.mes === m); return rs.length ? (opts.calc ? opts.calc(rs) : sum(rs, key)) : null; };
  const last = S.to, c = by(last);
  return `<div class="kpi"><div class="l">${label}</div><div class="v" title="Total del rango seleccionado">${value}</div>
  <div class="d"><span title="${mLabel(last)} vs ${mLabel(shift(last, -1))}">MoM ${delta(c, by(shift(last, -1)), opts.invert)}</span>
  <span title="${mLabel(last)} vs ${mLabel(shift(last, -12))}">YoY ${delta(c, by(shift(last, -12)), opts.invert)}</span>
  ${opts.extra ? `<span class="mut">${opts.extra}</span>` : ''}</div></div>`; }

// ---------- Tablas ordenables + export CSV ----------
const TABLES = {};
function table(id, title, sub, cols, rows) {
  TABLES[id] = { cols, rows, sort: TABLES[id]?.sort || null, title };
  return `<div class="card s12" id="${id}"><div class="hd"><div><h3>${title}</h3><div class="sub">${sub}</div></div>
    <button class="btn" data-csv="${id}">⬇ Exportar CSV</button></div><div class="tbl"></div></div>`; }
function drawTable(id) {
  const t = TABLES[id], el = $(`#${id} .tbl`); if (!el) return;
  let rows = [...t.rows]; if (t.sort) { const { k, dir } = t.sort; rows.sort((a, b) => (a[k] > b[k] ? 1 : a[k] < b[k] ? -1 : 0) * dir); }
  el.innerHTML = `<table><thead><tr>${t.cols.map(c => `<th data-k="${c.k}">${c.h}${t.sort?.k === c.k ? (t.sort.dir > 0 ? ' ▲' : ' ▼') : ''}</th>`).join('')}</tr></thead>
  <tbody>${rows.map(r => `<tr>${t.cols.map(c => `<td>${c.f ? c.f(r[c.k], r) : r[c.k]}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  el.querySelectorAll('th').forEach(th => th.onclick = () => { const k = th.dataset.k; t.sort = { k, dir: t.sort?.k === k ? -t.sort.dir : -1 }; drawTable(id); }); }
function exportCSV(id) {
  const t = TABLES[id], money = c => c.money;
  const head = t.cols.map(c => c.h + (money(c) ? ` (${S.ccy})` : '')).join(';');
  const body = t.rows.map(r => t.cols.map(c => { let v = r[c.k]; if (money(c)) v = conv(v).toFixed(2); else if (c.pct) v = (v * 100).toFixed(2); return String(v).replace('.', ','); }).join(';')).join('\n');
  const blob = new Blob(['\ufeff' + head + '\n' + body], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `${id}_${S.from}_${S.to}_${S.ccy}.csv`; a.click(); toast('CSV exportado'); }

// ---------- Charts ----------
function chart(id, opt, onClick) {
  const el = document.getElementById(id); if (!el) return;
  const c = echarts.init(el, S.theme === 'dark' ? 'dark' : null, { renderer: 'canvas' });
  const fg = css('--fg'), mut = css('--mut'), bd = css('--bd');
  c.setOption(Object.assign({ backgroundColor: 'transparent', color: PAL, textStyle: { color: fg },
    tooltip: { trigger: 'axis', confine: true, valueFormatter: v => typeof v === 'number' ? full(v) : v },
    legend: { top: 0, textStyle: { color: mut }, type: 'scroll' }, grid: { left: 8, right: 12, top: 52, bottom: 8, containLabel: true } }, opt));
  const ax = { axisLabel: { color: mut }, splitLine: { lineStyle: { color: bd } }, axisLine: { lineStyle: { color: bd } } };
  if (opt.xAxis) c.setOption({ xAxis: [].concat(opt.xAxis).map(() => ax), yAxis: [].concat(opt.yAxis).map(() => ax) });
  if (onClick) c.on('click', onClick);
  charts.push(c); }
const moneyAxis = (extra = {}) => Object.assign({ type: 'value', name: S.ccy, nameTextStyle: { color: css('--mut') }, axisLabel: { formatter: v => fmt(v, false) } }, extra);
const pctAxis = (extra = {}) => Object.assign({ type: 'value', axisLabel: { formatter: v => v + '%' }, splitLine: { show: false } }, extra);
const drillMonth = p => { const m = MONTHS.find(x => mLabel(x) === p.name); if (m) { S.from = S.to = m; toast(`Detalle de ${mLabel(m)} · usá "Todo" para volver`); render(); } };
const card = (cls, id, title, sub) => `<div class="card ${cls}"><h3>${title}</h3><div class="sub">${sub}</div><div class="chart" id="${id}"></div></div>`;
const select = (key, label, opts) => `<label>${label} <select data-f="${key}"><option value="">Todos</option>${opts.map(o => `<option ${S[key] === o ? 'selected' : ''}>${o}</option>`).join('')}</select></label>`;
const chips = keys => keys.filter(k => S[k]).map(k => `<span class="chip" data-clear="${k}" title="Quitar filtro">${S[k]} ✕</span>`).join('');
const uniq = (k, f) => [...new Set(D[k].map(r => r[f]))];

// ---------- FINANCIERO ----------
function financiero() {
  const er = rng('financiero_estado_resultados'), fc = rng('financiero_flujo_caja'), pr = rng('financiero_presupuesto_vs_real'), ms = months();
  const ing = sum(er, 'ingresos_ars'), ub = sum(er, 'utilidad_bruta_ars'), eb = sum(er, 'ebitda_ars'), rn = sum(er, 'resultado_neto_ars');
  const ER = D.financiero_estado_resultados, cajaFin = fc.length ? fc[fc.length - 1].saldo_caja_ars : 0;
  let h = kpi('Ingresos', fmt(ing), ER, 'ingresos_ars')
    + kpi('Margen bruto', pct(ub / ing), ER, '', { calc: r => r[0].utilidad_bruta_ars / r[0].ingresos_ars, extra: fmt(ub) })
    + kpi('EBITDA', fmt(eb), ER, 'ebitda_ars', { extra: 'margen del período ' + pct(eb / ing) })
    + kpi('Resultado neto', fmt(rn), ER, 'resultado_neto_ars', { extra: 'caja final ' + fmt(cajaFin) });
  h += card('s7', 'c-trend', 'Ingresos, EBITDA y margen EBITDA mensual', 'Margen = EBITDA del mes / ingresos del mes · clic en un mes para ver su detalle (drill-down)')
     + card('s5', 'c-wf', 'Estado de resultados (cascada)', `Acumulado ${mLabel(S.from)} – ${mLabel(S.to)}`)
     + card('s7', 'c-cash', 'Flujo de caja', 'Operativo antes de CT + var. capital de trabajo + inversiones + financiero = flujo neto · línea: saldo de caja al cierre')
     + card('s5', 'c-bud', 'Presupuesto vs real', 'Acumulado por concepto; clic en una barra para ver su evolución');
  const concs = uniq('financiero_presupuesto_vs_real', 'concepto');
  const agg = concs.map(c => { const rs = pr.filter(r => r.concepto === c), p = sum(rs, 'presupuesto_ars'), r = sum(rs, 'real_ars'); return { concepto: c, presupuesto: p, real: r, var: r - p, varp: (r - p) / p }; });
  h += table('t-pl', 'Estado de resultados mensual', 'Todos los meses del rango · ordená haciendo clic en cada columna', [
    { k: 'mes', h: 'Mes', f: mLabel }, ...[['ingresos_ars', 'Ingresos'], ['costo_ventas_ars', 'Costo de ventas'], ['utilidad_bruta_ars', 'Utilidad bruta'], ['gastos_operativos_ars', 'Gastos operativos'], ['ebitda_ars', 'EBITDA'], ['resultado_neto_ars', 'Resultado neto']].map(([k, h]) => ({ k, h, money: 1, f: full })),
    { k: 'mebitda', h: 'Margen EBITDA (mes)', pct: 1, f: v => pct(v) }, { k: 'margen', h: 'Margen neto (mes)', pct: 1, f: v => pct(v) }], er.map(r => ({ ...r, mebitda: r.ebitda_ars / r.ingresos_ars, margen: r.resultado_neto_ars / r.ingresos_ars })))
   + table('t-bud', 'Presupuesto vs real', 'Variación positiva en costos/gastos = desvío desfavorable', [
    { k: 'concepto', h: 'Concepto' }, { k: 'presupuesto', h: 'Presupuesto', money: 1, f: full }, { k: 'real', h: 'Real', money: 1, f: full }, { k: 'var', h: 'Variación', money: 1, f: full }, { k: 'varp', h: 'Var. %', pct: 1, f: v => pct(v) }], agg);
  $('#main').innerHTML = h;
  chart('c-trend', { xAxis: { type: 'category', data: ms.map(mLabel) }, yAxis: [moneyAxis(), pctAxis()],
    tooltip: { trigger: 'axis', confine: true, formatter: ps => ps[0].name + '<br>' + ps.map(p => `${p.marker}${p.seriesName}: <b>${p.seriesIndex === 2 ? p.value + '%' : full(p.value)}</b>`).join('<br>') },
    series: [{ name: 'Ingresos', type: 'bar', data: er.map(r => r.ingresos_ars) }, { name: 'EBITDA', type: 'bar', data: er.map(r => r.ebitda_ars) },
      { name: 'Margen EBITDA mensual', type: 'line', yAxisIndex: 1, smooth: true, data: er.map(r => +(r.ebitda_ars / r.ingresos_ars * 100).toFixed(1)) }] }, drillMonth);
  const steps = [['Ingresos', ing], ['Costo ventas', -sum(er, 'costo_ventas_ars')], ['Gastos op.', -sum(er, 'gastos_operativos_ars')], ['Depreciación', -sum(er, 'depreciacion_ars')], ['Res. financiero', sum(er, 'resultado_financiero_ars')], ['Impuestos', -sum(er, 'impuesto_ars')]];
  let acc = 0; const base = [], val = [];
  steps.forEach(([n, v], i) => { if (i === 0) { base.push(0); val.push(v); acc = v; } else { acc += v; base.push(v < 0 ? acc : acc - v); val.push(Math.abs(v)); } });
  base.push(0); val.push(rn);
  const cats = [...steps.map(s => s[0]), 'Resultado neto'];
  chart('c-wf', { xAxis: { type: 'category', data: cats, axisLabel: { interval: 0, rotate: 30 } }, yAxis: moneyAxis(), legend: { show: false },
    tooltip: { trigger: 'axis', confine: true, formatter: ps => { const i = ps[0].dataIndex; const v = i < steps.length ? steps[i][1] : rn; return `${cats[i]}: <b>${full(v)}</b><br>${pct(v / ing)} de ingresos`; } },
    series: [{ type: 'bar', stack: 'w', itemStyle: { color: 'transparent' }, data: base },
      { type: 'bar', stack: 'w', data: val.map((v, i) => ({ value: v, itemStyle: { color: i === 0 || i === cats.length - 1 ? PAL[0] : (steps[i] && steps[i][1] >= 0 ? PAL[1] : '#dc2626') } })) }] });
  chart('c-cash', { xAxis: { type: 'category', data: ms.map(mLabel) }, yAxis: [moneyAxis(), moneyAxis({ splitLine: { show: false } })],
    series: [['flujo_operativo_ars', 'Operativo (antes de CT)'], ['variacion_ct_ars', 'Var. capital de trabajo'], ['inversiones_ars', 'Inversiones'], ['flujo_financiero_ars', 'Financiero']].map(([k, n]) => ({ name: n, type: 'bar', stack: 'f', data: fc.map(r => r[k]) }))
      .concat([{ name: 'Saldo de caja', type: 'line', yAxisIndex: 1, smooth: true, data: fc.map(r => r.saldo_caja_ars) }, { name: 'Flujo neto', type: 'line', symbol: 'diamond', symbolSize: 8, lineStyle: { width: 0 }, itemStyle: { color: css('--fg') }, data: fc.map(r => r.flujo_neto_ars) }]) }, drillMonth);
  chart('c-bud', { xAxis: { type: 'category', data: concs, axisLabel: { interval: 0, rotate: 25 } }, yAxis: moneyAxis(),
    series: [{ name: 'Presupuesto', type: 'bar', data: agg.map(a => a.presupuesto), itemStyle: { color: '#94a3b8' } }, { name: 'Real', type: 'bar', data: agg.map(a => a.real) }] },
    p => { const c = p.name, rs = pr.filter(r => r.concepto === c); TABLES['t-bud'].title = c;
      const el = document.getElementById('c-bud'); echarts.getInstanceByDom(el).setOption({ xAxis: { data: ms.map(mLabel), axisLabel: { rotate: 0 } }, series: [{ data: rs.map(r => r.presupuesto_ars) }, { data: rs.map(r => r.real_ars) }] });
      el.previousElementSibling.textContent = `${c} por mes · cambiá cualquier filtro para volver`; });
}

// ---------- VENTAS ----------
function ventas() {
  const vm = rng('ventas_mensual'), ms = months();
  const vp = rng('ventas_por_producto'), vr = rng('ventas_por_region'), vc = rng('ventas_por_canal');
  const tot = sum(vm, 'ventas_netas_ars'), un = sum(vm, 'unidades');
  const VC = D.ventas_por_canal, ecom = sum(vc.filter(r => r.canal === 'E-commerce'), 'ventas_ars') / sum(vc, 'ventas_ars');
  let h = `<div class="card drill">${select('producto', 'Producto', uniq('ventas_por_producto', 'producto'))}${select('region', 'Región', uniq('ventas_por_region', 'region'))}${select('canal', 'Canal', uniq('ventas_por_canal', 'canal'))}
    <span class="mut">Filtros de segmento: también podés hacer clic en los gráficos.</span>${chips(['producto', 'region', 'canal'])}</div>`;
  h += kpi('Ventas netas (= ingresos P&L)', fmt(tot), D.ventas_mensual, 'ventas_netas_ars')
    + kpi('Unidades', num(un), D.ventas_mensual, 'unidades')
    + kpi('Ticket promedio', fmt(tot / un), D.ventas_mensual, '', { calc: r => r[0].ventas_netas_ars / r[0].unidades })
    + kpi('Participación e-commerce', pct(ecom), VC, '', { calc: r => sum(r.filter(x => x.canal === 'E-commerce'), 'ventas_ars') / sum(r, 'ventas_ars') });
  const segTitle = [S.producto, S.region, S.canal].filter(Boolean).join(' · ') || 'Total compañía';
  h += card('s8', 'c-vt', `Tendencia de ventas — ${segTitle}`, 'Línea punteada: promedio móvil 3 meses · clic en un mes para drill-down')
     + card('s4', 'c-vch', 'Ventas por canal', 'Clic para filtrar')
     + card('s6', 'c-vp', 'Ventas por producto', 'Clic en una barra para filtrar la tendencia')
     + card('s6', 'c-vr', 'Ventas por región', 'Clic en una barra para filtrar la tendencia');
  const byProd = uniq('ventas_por_producto', 'producto').map(p => { const rs = vp.filter(r => r.producto === p); return { producto: p, sku: rs[0]?.sku, ventas: sum(rs, 'ventas_ars'), unidades: sum(rs, 'unidades') }; })
    .map(r => ({ ...r, precio: r.ventas / r.unidades, share: r.ventas / sum(vp, 'ventas_ars') }));
  h += table('t-prod', 'Detalle por producto', `Rango ${mLabel(S.from)} – ${mLabel(S.to)}`, [{ k: 'producto', h: 'Producto' }, { k: 'sku', h: 'SKU' }, { k: 'ventas', h: 'Ventas', money: 1, f: full }, { k: 'unidades', h: 'Unidades', f: num }, { k: 'precio', h: 'Precio prom.', money: 1, f: full }, { k: 'share', h: 'Participación', pct: 1, f: v => pct(v) }], byProd)
    + table('t-cli', 'Top clientes (últimos 12 meses)', 'Ranking fijo de 12 meses; no depende del filtro de fechas', [{ k: 'ranking', h: '#' }, { k: 'cliente', h: 'Cliente' }, { k: 'cliente_id', h: 'ID' }, { k: 'ventas_12m_ars', h: 'Ventas 12m', money: 1, f: full }], D.ventas_top_clientes);
  $('#main').innerHTML = h;
  // serie de tendencia según segmento elegido (cada dimensión es una tabla independiente)
  let seg = vm.map(r => r.ventas_netas_ars), segName = 'Ventas netas';
  if (S.producto) { seg = ms.map(m => sum(vp.filter(r => r.mes === m && r.producto === S.producto), 'ventas_ars')); segName = S.producto; }
  else if (S.region) { seg = ms.map(m => sum(vr.filter(r => r.mes === m && r.region === S.region), 'ventas_ars')); segName = S.region; }
  else if (S.canal) { seg = ms.map(m => sum(vc.filter(r => r.mes === m && r.canal === S.canal), 'ventas_ars')); segName = S.canal; }
  const ma = seg.map((_, i) => i < 2 ? null : (seg[i] + seg[i - 1] + seg[i - 2]) / 3);
  const extra = [S.producto && S.region && 'producto', S.region && S.canal && 'región'].filter(Boolean);
  const series = [{ name: segName, type: 'line', areaStyle: { opacity: .15 }, smooth: true, data: seg }, { name: 'Prom. móvil 3M', type: 'line', lineStyle: { type: 'dashed' }, symbol: 'none', data: ma }];
  if (S.producto && S.region) series.push({ name: S.region, type: 'line', smooth: true, data: ms.map(m => sum(vr.filter(r => r.mes === m && r.region === S.region), 'ventas_ars')) });
  if (S.canal && (S.producto || S.region)) series.push({ name: S.canal, type: 'line', smooth: true, data: ms.map(m => sum(vc.filter(r => r.mes === m && r.canal === S.canal), 'ventas_ars')) });
  chart('c-vt', { xAxis: { type: 'category', data: ms.map(mLabel) }, yAxis: moneyAxis(), series }, drillMonth);
  const chans = uniq('ventas_por_canal', 'canal');
  chart('c-vch', { tooltip: { trigger: 'item', confine: true, formatter: p => `${p.name}: <b>${full(p.value)}</b> (${p.percent}%)` }, legend: { bottom: 0, top: 'auto', textStyle: { color: css('--mut') } },
    series: [{ type: 'pie', radius: ['45%', '72%'], center: ['50%', '45%'], label: { show: false }, data: chans.map(c => ({ name: c, value: sum(vc.filter(r => r.canal === c), 'ventas_ars'), selected: S.canal === c })), selectedMode: 'single' }] },
    p => { S.canal = S.canal === p.name ? '' : p.name; render(); });
  const sel = (n, k) => S[k] && S[k] !== n ? { opacity: .35 } : {};
  const hbar = (id, list, k) => chart(id, { xAxis: moneyAxis(), yAxis: { type: 'category', inverse: true, data: list.map(x => x.n) }, legend: { show: false }, tooltip: { trigger: 'axis', confine: true, valueFormatter: full },
    series: [{ type: 'bar', name: 'Ventas', data: list.map((x, i) => ({ value: x.v, itemStyle: { color: PAL[i % PAL.length], ...sel(x.n, k) } })), label: { show: true, position: 'insideRight', color: '#fff', formatter: p => fmt(p.value) } }] },
    p => { S[k] = S[k] === p.name ? '' : p.name; render(); });
  hbar('c-vp', byProd.map(r => ({ n: r.producto, v: r.ventas })).sort((a, b) => b.v - a.v), 'producto');
  hbar('c-vr', uniq('ventas_por_region', 'region').map(n => ({ n, v: sum(vr.filter(r => r.region === n), 'ventas_ars') })).sort((a, b) => b.v - a.v), 'region');
}

// ---------- COSTOS ----------
function costos() {
  const fv = rng('costos_fijo_variable'), cc = rng('costos_por_centro'), cu = rng('costos_unitarios'), cv = rng('costos_variaciones'), ms = months();
  const tot = sum(fv, 'costo_total_ars'), fij = sum(fv, 'costos_fijos_ars'), un = sum(fv, 'unidades_producidas');
  const varTot = sum(cv, 'variacion_ars'), std = sum(cv, 'costo_estandar_ars');
  let h = `<div class="card drill">${select('centro', 'Centro de costo', uniq('costos_por_centro', 'centro_costo'))}${select('sku', 'Producto', uniq('costos_unitarios', 'producto'))}
    <span class="mut">Clic en el gráfico de centros o en un producto para filtrar.</span>${chips(['centro', 'sku'])}</div>`;
  h += kpi('Costo total', fmt(tot), D.costos_fijo_variable, 'costo_total_ars', { invert: true })
    + kpi('Estructura fija', pct(fij / tot), D.costos_fijo_variable, '', { calc: r => r[0].costos_fijos_ars / r[0].costo_total_ars, invert: true, extra: 'variable ' + pct(1 - fij / tot) })
    + kpi('Desvío vs estándar', fmt(varTot), D.costos_variaciones, 'variacion_ars', { invert: true, extra: pct(varTot / std) })
    + kpi('Costo por unidad vendida', fmt(tot / un), D.costos_fijo_variable, '', { calc: r => r[0].costo_total_ars / r[0].unidades_producidas, invert: true });
  h += card('s7', 'c-fv', 'Costos fijos vs variables', 'Costo total = costo de ventas + gastos operativos (P&L, sin depreciación) · línea: costo por unidad vendida · clic en un mes para drill-down')
     + card('s5', 'c-cc', `Costos por centro${S.centro ? ' — ' + S.centro : ''}`, 'Distribución en el rango; clic para filtrar')
     + card('s6', 'c-var', 'Costo estándar vs real', 'Barras: desvío % (rojo = desfavorable)')
     + card('s6', 'c-cu', `Costo unitario por producto${S.sku ? ' — ' + S.sku : ''}`, 'Evolución del costo unitario');
  const prods = uniq('costos_unitarios', 'producto');
  const rows = prods.map(p => { const rs = cu.filter(r => r.producto === p); if (!rs.length) return null; const a = rs[0], b = rs[rs.length - 1];
    return { producto: p, sku: a.sku, ini: a.costo_unitario_ars, fin: b.costo_unitario_ars, var: (b.costo_unitario_ars - a.costo_unitario_ars) / a.costo_unitario_ars, unidades: sum(rs, 'unidades'), costo: sum(rs, 'costo_ventas_ars') }; }).filter(Boolean);
  h += table('t-cu', 'Costos unitarios por producto', `Σ costo de ventas por SKU = costo de ventas del P&L · variación entre ${mLabel(S.from)} y ${mLabel(S.to)}`, [{ k: 'producto', h: 'Producto' }, { k: 'sku', h: 'SKU' }, { k: 'ini', h: 'Costo unit. inicial', money: 1, f: full }, { k: 'fin', h: 'Costo unit. final', money: 1, f: full }, { k: 'var', h: 'Var. %', pct: 1, f: v => pct(v) }, { k: 'unidades', h: 'Unidades', f: num }, { k: 'costo', h: 'Costo de ventas', money: 1, f: full }], rows)
    + table('t-var', 'Análisis de variaciones mensual', 'Real vs estándar', [{ k: 'mes', h: 'Mes', f: mLabel }, { k: 'costo_estandar_ars', h: 'Estándar', money: 1, f: full }, { k: 'costo_real_ars', h: 'Real', money: 1, f: full }, { k: 'variacion_ars', h: 'Variación', money: 1, f: full }, { k: 'p', h: 'Var. %', pct: 1, f: v => pct(v) }], cv.map(r => ({ ...r, p: r.variacion_pct / 100 })));
  $('#main').innerHTML = h;
  chart('c-fv', { xAxis: { type: 'category', data: ms.map(mLabel) }, yAxis: [moneyAxis(), moneyAxis({ splitLine: { show: false } })],
    series: [{ name: 'Fijos', type: 'bar', stack: 'c', data: fv.map(r => r.costos_fijos_ars) }, { name: 'Variables', type: 'bar', stack: 'c', data: fv.map(r => r.costos_variables_ars) },
      { name: 'Costo por unidad', type: 'line', yAxisIndex: 1, smooth: true, data: fv.map(r => r.costo_total_ars / r.unidades_producidas) }] }, drillMonth);
  const centros = uniq('costos_por_centro', 'centro_costo');
  if (S.centro) chart('c-cc', { xAxis: { type: 'category', data: ms.map(mLabel) }, yAxis: moneyAxis(), series: [{ name: S.centro, type: 'bar', data: ms.map(m => sum(cc.filter(r => r.mes === m && r.centro_costo === S.centro), 'costo_ars')) }] }, () => { S.centro = ''; render(); });
  else chart('c-cc', { tooltip: { trigger: 'item', confine: true, formatter: p => `${p.name}: <b>${full(p.value)}</b> (${p.percent}%)` }, legend: { bottom: 0, top: 'auto', textStyle: { color: css('--mut') } },
    series: [{ type: 'pie', radius: ['45%', '72%'], center: ['50%', '45%'], label: { formatter: '{d}%' }, data: centros.map(c => ({ name: c, value: sum(cc.filter(r => r.centro_costo === c), 'costo_ars') })) }] },
    p => { S.centro = p.name; render(); });
  chart('c-var', { xAxis: { type: 'category', data: ms.map(mLabel) }, yAxis: [moneyAxis(), pctAxis()],
    tooltip: { trigger: 'axis', confine: true, formatter: ps => ps[0].name + '<br>' + ps.map(p => `${p.marker}${p.seriesName}: <b>${p.seriesIndex === 2 ? p.value + '%' : full(p.value)}</b>`).join('<br>') },
    series: [{ name: 'Estándar', type: 'line', smooth: true, data: cv.map(r => r.costo_estandar_ars) }, { name: 'Real', type: 'line', smooth: true, data: cv.map(r => r.costo_real_ars) },
      { name: 'Desvío %', type: 'bar', yAxisIndex: 1, data: cv.map(r => ({ value: r.variacion_pct, itemStyle: { color: r.variacion_pct > 0 ? '#dc2626' : '#16a34a', opacity: .55 } })) }] });
  const shown = S.sku ? [S.sku] : prods;
  chart('c-cu', { xAxis: { type: 'category', data: ms.map(mLabel) }, yAxis: moneyAxis({ scale: true }),
    series: shown.map(p => ({ name: p, type: 'line', smooth: true, symbolSize: 4, data: ms.map(m => (cu.find(r => r.mes === m && r.producto === p) || {}).costo_unitario_ars ?? null) })) },
    p => { S.sku = S.sku ? '' : p.seriesName; render(); });
}

// ---------- Render y estado ----------
function render() {
  charts.forEach(c => c.dispose()); charts = [];
  document.documentElement.dataset.theme = S.theme;
  document.querySelectorAll('.tab').forEach(b => b.classList.toggle('on', b.dataset.tab === S.tab));
  document.querySelectorAll('#ccy button').forEach(b => b.classList.toggle('on', b.dataset.c === S.ccy));
  const n = months().length; document.querySelectorAll('#presets button').forEach(b => b.classList.toggle('on', S.to === MONTHS.at(-1) && (+b.dataset.p === n || (+b.dataset.p === 0 && n === MONTHS.length))));
  $('#from').value = S.from; $('#to').value = S.to;
  const fx = D.fx; $('#fxnote').innerHTML = `Tipo de cambio: <b>1 USD = ${fx.ars_per_usd.toLocaleString('es-AR')} ARS</b> · ${fx.tipo} · ${fx.fuente} · al ${fx.fecha.split('-').reverse().join('/')}${fx.fallback ? ' (valor de respaldo)' : ''}. Montos en USD convertidos a tipo de cambio único (ilustrativo). MM = millones · mil M = miles de millones. Los márgenes de las tarjetas KPI son del período seleccionado (acumulado); los de gráficos y tablas, mensuales.`;
  ({ financiero, ventas, costos })[S.tab]();
  Object.keys(TABLES).forEach(id => document.getElementById(id) ? drawTable(id) : delete TABLES[id]);
  location.hash = `${S.tab}`;
}
async function init() {
  D = await (await fetch('data/data.json')).json();
  $('#empresa').textContent = D.empresa;
  MONTHS = D.ventas_mensual.map(r => r.mes);
  S.to = MONTHS.at(-1); S.from = MONTHS.at(-12) || MONTHS[0];
  const h = location.hash.slice(1); if (['financiero', 'ventas', 'costos'].includes(h)) S.tab = h;
  const opts = MONTHS.map(m => `<option value="${m}">${mLabel(m)}</option>`).join(''); $('#from').innerHTML = opts; $('#to').innerHTML = opts;
  $('#from').onchange = e => { S.from = e.target.value; if (S.from > S.to) S.to = S.from; render(); };
  $('#to').onchange = e => { S.to = e.target.value; if (S.to < S.from) S.from = S.to; render(); };
  document.querySelectorAll('.tab').forEach(b => b.onclick = () => { S.tab = b.dataset.tab; render(); });
  document.querySelectorAll('#ccy button').forEach(b => b.onclick = () => { S.ccy = b.dataset.c; render(); });
  document.querySelectorAll('#presets button').forEach(b => b.onclick = () => { const p = +b.dataset.p; S.to = MONTHS.at(-1); S.from = p ? MONTHS.at(-p) : MONTHS[0]; render(); });
  $('#theme').onclick = () => { S.theme = S.theme === 'dark' ? 'light' : 'dark'; localStorage.setItem('theme', S.theme); render(); };
  $('#main').addEventListener('change', e => { const k = e.target.dataset.f; if (k) { S[k] = e.target.value; render(); } });
  $('#main').addEventListener('click', e => { const t = e.target.closest('[data-csv],[data-clear]'); if (!t) return; if (t.dataset.csv) exportCSV(t.dataset.csv); else { S[t.dataset.clear] = ''; render(); } });
  window.addEventListener('resize', () => charts.forEach(c => c.resize()));
  render();
}
init();
