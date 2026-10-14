#!/usr/bin/env python3
"""Genera datos ficticios (24 meses) para NovaCampo Alimentos S.A."""

from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from fx import ars_to_usd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"

SEED = 42
MONTHS = 24
COMPANY = "NovaCampo Alimentos S.A."

BCRA_MONETARIAS_URL = (
    "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/5?limit=1"
)
BCRA_VARIABLE_ID = 5
BCRA_RATE_LABEL = (
    "Tipo de cambio mayorista de referencia (Comunicación A 3500)"
)

FALLBACK_ARS_PER_USD = 1200.0
FALLBACK_DATE = "2025-01-15"

PRODUCTS = [
    ("NC-001", "Yerba mate premium 1kg"),
    ("NC-002", "Aceite de girasol 900ml"),
    ("NC-003", "Arroz largo fino 1kg"),
    ("NC-004", "Harina 000 1kg"),
    ("NC-005", "Dulce de leche 450g"),
    ("NC-006", "Galletitas surtidas 300g"),
]

CHANNELS = ["Mayorista", "Retail", "E-commerce", "Venta directa"]
REGIONS = ["CABA", "GBA Norte", "GBA Sur", "Córdoba", "Rosario", "Mendoza"]

CLIENTS = [
    ("CLI-101", "Supermercados Don Horacio S.A."),
    ("CLI-102", "Distribuidora La Ribera S.R.L."),
    ("CLI-103", "Almacén El Fogón"),
    ("CLI-104", "Grupo Norte Retail S.A."),
    ("CLI-105", "Mercado Online Pampero"),
    ("CLI-106", "Mayorista San Martín"),
    ("CLI-107", "Cooperativa Valle Verde"),
    ("CLI-108", "Bodegón Central"),
    ("CLI-109", "Hipermercado Andino"),
    ("CLI-110", "Cadenas del Sur S.A."),
]

COST_CENTERS = [
    ("CC-01", "Producción"),
    ("CC-02", "Logística"),
    ("CC-03", "Comercial"),
    ("CC-04", "Administración"),
]


def fetch_bcra_reference_rate() -> dict:
    """Obtiene el último valor de la variable BCRA 5 (Com. A 3500)."""
    try:
        resp = requests.get(BCRA_MONETARIAS_URL, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        detalle = payload["results"][0]["detalle"][0]
        return {
            "ars_per_usd": float(detalle["valor"]),
            "fecha": detalle["fecha"],
            "fuente": f"API BCRA Estadísticas Monetarias v4.0 — variable {BCRA_VARIABLE_ID}",
            "tipo": BCRA_RATE_LABEL,
            "bcra_url": "https://www.bcra.gob.ar/",
            "fallback": False,
        }
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        return {
            "ars_per_usd": FALLBACK_ARS_PER_USD,
            "fecha": FALLBACK_DATE,
            "fuente": (
                f"Respaldo fijo ({FALLBACK_ARS_PER_USD} ARS/USD) — "
                f"no se pudo consultar BCRA: {exc}"
            ),
            "tipo": BCRA_RATE_LABEL,
            "bcra_url": "https://www.bcra.gob.ar/",
            "fallback": True,
        }


def month_range(n: int) -> list[pd.Timestamp]:
    end = pd.Timestamp(date.today()).replace(day=1)
    start = end - pd.DateOffset(months=n - 1)
    return list(pd.date_range(start=start, end=end, freq="MS"))


def write_exchange_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with (CONFIG_DIR / "exchange_rate.json").open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")


def generate_financiero(rng: random.Random, months: list[pd.Timestamp], rate: float) -> None:
    rows_pl = []
    rows_cf = []
    rows_bvr = []

    base_revenue = 85_000_000
    for i, m in enumerate(months):
        season = 1.0 + 0.12 * np.sin(2 * np.pi * i / 12)
        growth = 1.0 + 0.018 * i
        ingresos = base_revenue * season * growth * (1 + rng.uniform(-0.04, 0.04))
        cogs = ingresos * rng.uniform(0.52, 0.58)
        gross = ingresos - cogs
        opex = ingresos * rng.uniform(0.22, 0.28)
        ebitda = gross - opex
        dep = ingresos * 0.015
        ebit = ebitda - dep
        fin = ingresos * rng.uniform(-0.012, 0.008)
        imp = max(0, ebit * 0.25)
        net = ebit - fin - imp

        rows_pl.append(
            {
                "empresa": COMPANY,
                "mes": m.strftime("%Y-%m"),
                "ingresos_ars": round(ingresos, 2),
                "ingresos_usd": ars_to_usd(ingresos, rate),
                "costo_ventas_ars": round(cogs, 2),
                "costo_ventas_usd": ars_to_usd(cogs, rate),
                "utilidad_bruta_ars": round(gross, 2),
                "utilidad_bruta_usd": ars_to_usd(gross, rate),
                "gastos_operativos_ars": round(opex, 2),
                "gastos_operativos_usd": ars_to_usd(opex, rate),
                "ebitda_ars": round(ebitda, 2),
                "ebitda_usd": ars_to_usd(ebitda, rate),
                "depreciacion_ars": round(dep, 2),
                "depreciacion_usd": ars_to_usd(dep, rate),
                "resultado_operativo_ars": round(ebit, 2),
                "resultado_operativo_usd": ars_to_usd(ebit, rate),
                "resultado_financiero_ars": round(fin, 2),
                "resultado_financiero_usd": ars_to_usd(fin, rate),
                "impuesto_ars": round(imp, 2),
                "impuesto_usd": ars_to_usd(imp, rate),
                "resultado_neto_ars": round(net, 2),
                "resultado_neto_usd": ars_to_usd(net, rate),
            }
        )

        op_in = ebitda * rng.uniform(0.85, 0.95)
        op_out = cogs * 0.92 + opex * 0.88
        inv = ingresos * rng.uniform(-0.06, 0.04)
        fin_cf = fin * -1
        net_cf = op_in - op_out + inv + fin_cf
        rows_cf.append(
            {
                "empresa": COMPANY,
                "mes": m.strftime("%Y-%m"),
                "flujo_operativo_ars": round(op_in - op_out, 2),
                "flujo_operativo_usd": ars_to_usd(op_in - op_out, rate),
                "inversiones_ars": round(inv, 2),
                "inversiones_usd": ars_to_usd(inv, rate),
                "flujo_financiero_ars": round(fin_cf, 2),
                "flujo_financiero_usd": ars_to_usd(fin_cf, rate),
                "flujo_neto_ars": round(net_cf, 2),
                "flujo_neto_usd": ars_to_usd(net_cf, rate),
            }
        )

        for concepto, pct in [
            ("Ingresos", 1.0),
            ("Costo de ventas", cogs / ingresos),
            ("Gastos operativos", opex / ingresos),
            ("EBITDA", ebitda / ingresos),
        ]:
            pres = ingresos * pct * rng.uniform(0.95, 1.05)
            real = ingresos * pct
            rows_bvr.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "concepto": concepto,
                    "presupuesto_ars": round(pres, 2),
                    "presupuesto_usd": ars_to_usd(pres, rate),
                    "real_ars": round(real, 2),
                    "real_usd": ars_to_usd(real, rate),
                    "variacion_ars": round(real - pres, 2),
                    "variacion_pct": round((real - pres) / pres * 100, 2) if pres else 0,
                }
            )

    pd.DataFrame(rows_pl).to_csv(DATA_DIR / "financiero_estado_resultados.csv", index=False)
    pd.DataFrame(rows_cf).to_csv(DATA_DIR / "financiero_flujo_caja.csv", index=False)
    pd.DataFrame(rows_bvr).to_csv(DATA_DIR / "financiero_presupuesto_vs_real.csv", index=False)


def generate_ventas(rng: random.Random, months: list[pd.Timestamp], rate: float) -> None:
    monthly = []
    by_product = []
    by_channel = []
    by_region = []
    client_rows = []

    weights_ch = [0.38, 0.28, 0.18, 0.16]
    weights_reg = [0.22, 0.18, 0.14, 0.16, 0.15, 0.15]

    for i, m in enumerate(months):
        total = 85_000_000 * (1 + 0.018 * i) * (1 + rng.uniform(-0.05, 0.05))
        monthly.append(
            {
                "empresa": COMPANY,
                "mes": m.strftime("%Y-%m"),
                "ventas_netas_ars": round(total, 2),
                "ventas_netas_usd": ars_to_usd(total, rate),
                "unidades": int(total / 4500),
                "ticket_promedio_ars": round(total / max(1, int(total / 4500)), 2),
            }
        )

        prod_shares = np.array([rng.random() for _ in PRODUCTS], dtype=float)
        prod_shares /= prod_shares.sum()
        for (sku, name), share in zip(PRODUCTS, prod_shares):
            amt = total * share
            by_product.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "sku": sku,
                    "producto": name,
                    "ventas_ars": round(amt, 2),
                    "ventas_usd": ars_to_usd(amt, rate),
                    "unidades": int(amt / rng.uniform(800, 2500)),
                }
            )

        for ch, w in zip(CHANNELS, weights_ch):
            amt = total * w * (1 + rng.uniform(-0.08, 0.08))
            by_channel.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "canal": ch,
                    "ventas_ars": round(amt, 2),
                    "ventas_usd": ars_to_usd(amt, rate),
                }
            )

        for reg, w in zip(REGIONS, weights_reg):
            amt = total * w * (1 + rng.uniform(-0.1, 0.1))
            by_region.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "region": reg,
                    "ventas_ars": round(amt, 2),
                    "ventas_usd": ars_to_usd(amt, rate),
                }
            )

    for rank, (cid, cname) in enumerate(CLIENTS, start=1):
        base = rng.uniform(12_000_000, 48_000_000)
        client_rows.append(
            {
                "empresa": COMPANY,
                "cliente_id": cid,
                "cliente": cname,
                "ventas_12m_ars": round(base, 2),
                "ventas_12m_usd": ars_to_usd(base, rate),
                "ranking": rank,
            }
        )
    client_rows.sort(key=lambda x: x["ventas_12m_ars"], reverse=True)
    for i, row in enumerate(client_rows, start=1):
        row["ranking"] = i

    pd.DataFrame(monthly).to_csv(DATA_DIR / "ventas_mensual.csv", index=False)
    pd.DataFrame(by_product).to_csv(DATA_DIR / "ventas_por_producto.csv", index=False)
    pd.DataFrame(by_channel).to_csv(DATA_DIR / "ventas_por_canal.csv", index=False)
    pd.DataFrame(by_region).to_csv(DATA_DIR / "ventas_por_region.csv", index=False)
    pd.DataFrame(client_rows).to_csv(DATA_DIR / "ventas_top_clientes.csv", index=False)


def generate_costos(rng: random.Random, months: list[pd.Timestamp], rate: float) -> None:
    fv_rows = []
    cc_rows = []
    unit_rows = []
    var_rows = []

    for i, m in enumerate(months):
        vol = 18_000 + i * 350 + rng.randint(-800, 800)
        fixed = 22_000_000 * (1 + 0.01 * i)
        variable = vol * rng.uniform(2100, 2600)
        total = fixed + variable
        fv_rows.append(
            {
                "empresa": COMPANY,
                "mes": m.strftime("%Y-%m"),
                "costos_fijos_ars": round(fixed, 2),
                "costos_fijos_usd": ars_to_usd(fixed, rate),
                "costos_variables_ars": round(variable, 2),
                "costos_variables_usd": ars_to_usd(variable, rate),
                "costo_total_ars": round(total, 2),
                "costo_total_usd": ars_to_usd(total, rate),
                "unidades_producidas": vol,
            }
        )

        shares = [0.42, 0.28, 0.18, 0.12]
        for (cc_id, cc_name), sh in zip(COST_CENTERS, shares):
            amt = total * sh * (1 + rng.uniform(-0.05, 0.05))
            cc_rows.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "centro_costo_id": cc_id,
                    "centro_costo": cc_name,
                    "costo_ars": round(amt, 2),
                    "costo_usd": ars_to_usd(amt, rate),
                }
            )

        for sku, name in PRODUCTS[:4]:
            uc = rng.uniform(900, 1800) * (1 + 0.008 * i)
            unit_rows.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "sku": sku,
                    "producto": name,
                    "costo_unitario_ars": round(uc, 2),
                    "costo_unitario_usd": ars_to_usd(uc, rate),
                    "unidades": int(vol / len(PRODUCTS[:4])),
                }
            )

        std = total * rng.uniform(0.96, 1.02)
        var_rows.append(
            {
                "empresa": COMPANY,
                "mes": m.strftime("%Y-%m"),
                "costo_estandar_ars": round(std, 2),
                "costo_estandar_usd": ars_to_usd(std, rate),
                "costo_real_ars": round(total, 2),
                "costo_real_usd": ars_to_usd(total, rate),
                "variacion_ars": round(total - std, 2),
                "variacion_pct": round((total - std) / std * 100, 2) if std else 0,
            }
        )

    pd.DataFrame(fv_rows).to_csv(DATA_DIR / "costos_fijo_variable.csv", index=False)
    pd.DataFrame(cc_rows).to_csv(DATA_DIR / "costos_por_centro.csv", index=False)
    pd.DataFrame(unit_rows).to_csv(DATA_DIR / "costos_unitarios.csv", index=False)
    pd.DataFrame(var_rows).to_csv(DATA_DIR / "costos_variaciones.csv", index=False)


def main() -> None:
    rng = random.Random(SEED)
    np.random.seed(SEED)

    cfg = fetch_bcra_reference_rate()
    write_exchange_config(cfg)
    rate = cfg["ars_per_usd"]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    months = month_range(MONTHS)

    generate_financiero(rng, months, rate)
    generate_ventas(rng, months, rate)
    generate_costos(rng, months, rate)

    print(f"Datos generados en {DATA_DIR} ({MONTHS} meses).")
    print(
        f"Cotización: {rate} ARS/USD ({cfg['fecha']}) — "
        f"{'respaldo' if cfg.get('fallback') else 'BCRA'}"
    )


if __name__ == "__main__":
    main()
