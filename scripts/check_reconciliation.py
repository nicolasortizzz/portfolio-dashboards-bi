#!/usr/bin/env python3
"""Controles de conciliación entre datasets. Sale con código 1 si algo no cierra.

Tolerancia: 0,01 ARS por partida (redondeo a centavos)."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

D = Path(__file__).resolve().parents[1] / "data"
r = lambda f: pd.read_csv(D / f"{f}.csv")
pl, cf, bvr = r("financiero_estado_resultados"), r("financiero_flujo_caja"), r("financiero_presupuesto_vs_real")
vm, vp, vc, vr, cli = r("ventas_mensual"), r("ventas_por_producto"), r("ventas_por_canal"), r("ventas_por_region"), r("ventas_top_clientes")
fv, cc, cu, cv = r("costos_fijo_variable"), r("costos_por_centro"), r("costos_unitarios"), r("costos_variaciones")
P = pl.set_index("mes")
TOL = 0.011
fails, checks = [], 0

def chk(name, a, b, tol=TOL):
    global checks
    a, b = a.reindex(P.index), b.reindex(P.index)
    d = (a - b).abs()
    checks += len(d)
    bad = d[(d > tol) | d.isna()]
    status = "OK " if bad.empty else "FALLA"
    print(f"[{status}] {name}: {len(d)} meses, desvío máx {d.max():,.2f} ARS")
    if not bad.empty:
        fails.append((name, bad.to_dict()))

g = lambda df, col: df.groupby("mes")[col].sum()
# P&L interno
chk("P&L: utilidad bruta = ingresos − costo de ventas", P.utilidad_bruta_ars, P.ingresos_ars - P.costo_ventas_ars)
chk("P&L: EBITDA = utilidad bruta − gastos operativos", P.ebitda_ars, P.utilidad_bruta_ars - P.gastos_operativos_ars)
chk("P&L: resultado operativo = EBITDA − depreciación", P.resultado_operativo_ars, P.ebitda_ars - P.depreciacion_ars)
chk("P&L: neto = operativo + resultado financiero (con signo) − impuesto", P.resultado_neto_ars, P.resultado_operativo_ars + P.resultado_financiero_ars - P.impuesto_ars, 0.03)
# Flujo de caja
C = cf.set_index("mes")
chk("Caja: operativo (antes de CT) = neto + depreciación", C.flujo_operativo_ars, P.resultado_neto_ars + P.depreciacion_ars)
chk("Caja: neto = operativo + var. CT + inversiones + financiero", C.flujo_neto_ars, C.flujo_operativo_ars + C.variacion_ct_ars + C.inversiones_ars + C.flujo_financiero_ars, 0.03)
chk("Caja: saldo = saldo anterior + flujo neto (saldo inicial 42 MM)", C.saldo_caja_ars, C.saldo_caja_ars.shift(1).fillna(42_000_000) + C.flujo_neto_ars, 0.03)
# Presupuesto vs real
for conc, col in [("Ingresos", "ingresos_ars"), ("Costo de ventas", "costo_ventas_ars"), ("Gastos operativos", "gastos_operativos_ars"), ("EBITDA", "ebitda_ars")]:
    chk(f"Ppto vs real: real '{conc}' = P&L", bvr[bvr.concepto == conc].set_index("mes").real_ars, P[col], 0.03)
# Ventas
chk("Ventas mensuales = ingresos P&L", vm.set_index("mes").ventas_netas_ars, P.ingresos_ars)
chk("Σ ventas por producto = ingresos P&L", g(vp, "ventas_ars"), P.ingresos_ars, 0.03)
chk("Σ ventas por canal = ingresos P&L", g(vc, "ventas_ars"), P.ingresos_ars, 0.03)
chk("Σ ventas por región = ingresos P&L", g(vr, "ventas_ars"), P.ingresos_ars, 0.03)
chk("Unidades mensuales = Σ unidades por producto", vm.set_index("mes").unidades.astype(float), g(vp, "unidades").astype(float))
# Costos
F = fv.set_index("mes")
chk("Costo total = costo de ventas + gastos operativos (P&L)", F.costo_total_ars, P.costo_ventas_ars + P.gastos_operativos_ars, 0.03)
chk("Costo total = fijos + variables", F.costo_total_ars, F.costos_fijos_ars + F.costos_variables_ars, 0.03)
chk("Σ costos por centro = costo total", g(cc, "costo_ars"), F.costo_total_ars, 0.03)
chk("Costo real (variaciones) = costo total", cv.set_index("mes").costo_real_ars, F.costo_total_ars)
chk("Σ costo de ventas por SKU = costo de ventas P&L", g(cu, "costo_ventas_ars"), P.costo_ventas_ars, 0.03)
ltm = P.ingresos_ars.iloc[-12:].sum(); top = cli.ventas_12m_ars.sum(); checks += 1
ok = top <= ltm
print(f"[{'OK ' if ok else 'FALLA'}] Top 10 clientes 12m ({top:,.0f}) ≤ ingresos 12m ({ltm:,.0f}) — {top/ltm:.1%}")
if not ok: fails.append(("top clientes", {}))
print(f"\n{checks} controles mes a mes · {'TODO CONCILIA' if not fails else f'{len(fails)} CONTROLES FALLAN'}")
sys.exit(1 if fails else 0)
