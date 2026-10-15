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
        ingresos = round(base_revenue * season * growth * (1 + rng.uniform(-0.04, 0.04)), 2)
        cogs = round(ingresos * rng.uniform(0.52, 0.58), 2)
        gross = ingresos - cogs
        opex = round(ingresos * rng.uniform(0.22, 0.28), 2)
        ebitda = gross - opex
        dep = round(ingresos * 0.015, 2)
        ebit = ebitda - dep
        # Resultado financiero con signo (negativo = costo financiero neto)
        fin = round(ingresos * rng.uniform(-0.012, 0.008), 2)
        ebt = ebit + fin
        imp = round(max(0, ebt * 0.25), 2)
        net = ebt - imp

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

    saldo_caja = 42_000_000.0
    prev_wc = None
    for i, (m, pl_row) in enumerate(zip(months, rows_pl)):
        ingresos = pl_row["ingresos_ars"]
        cogs = pl_row["costo_ventas_ars"]
        opex = pl_row["gastos_operativos_ars"]
        ebitda = pl_row["ebitda_ars"]
        net = pl_row["resultado_neto_ars"]
        dep = pl_row["depreciacion_ars"]
        fin = pl_row["resultado_financiero_ars"]

        ar = ingresos * rng.uniform(0.38, 0.44)
        inventario = cogs * rng.uniform(0.22, 0.30)
        ap = cogs * rng.uniform(0.26, 0.34)
        wc = ar + inventario - ap
        delta_wc = 0.0 if prev_wc is None else wc - prev_wc
        prev_wc = wc

        # Flujo operativo ANTES de capital de trabajo: resultado neto + depreciación.
        # La variación de capital de trabajo se informa en su propia columna (no se suma dos veces):
        # flujo_neto = flujo_operativo + variacion_ct + inversiones + flujo_financiero
        flujo_operativo = round(net + dep, 2)
        delta_wc = round(delta_wc, 2)

        if i % 9 == 5:
            capex = -ingresos * rng.uniform(0.10, 0.16)
        elif rng.random() < 0.12:
            capex = -ingresos * rng.uniform(0.04, 0.07)
        else:
            capex = -ingresos * rng.uniform(0.008, 0.025)

        if i % 11 == 3:
            flujo_financiero = ingresos * rng.uniform(0.06, 0.11)
        elif i % 13 == 7:
            flujo_financiero = -ingresos * rng.uniform(0.04, 0.07)
        else:
            flujo_financiero = -fin * rng.uniform(0.4, 0.9)

        capex = round(capex, 2)
        flujo_financiero = round(flujo_financiero, 2)
        flujo_neto = round(flujo_operativo - delta_wc + capex + flujo_financiero, 2)
        saldo_caja = round(saldo_caja + flujo_neto, 2)

        rows_cf.append(
            {
                "empresa": COMPANY,
                "mes": m.strftime("%Y-%m"),
                "flujo_operativo_ars": round(flujo_operativo, 2),
                "flujo_operativo_usd": ars_to_usd(flujo_operativo, rate),
                "variacion_ct_ars": round(-delta_wc, 2),
                "variacion_ct_usd": ars_to_usd(-delta_wc, rate),
                "inversiones_ars": round(capex, 2),
                "inversiones_usd": ars_to_usd(capex, rate),
                "flujo_financiero_ars": round(flujo_financiero, 2),
                "flujo_financiero_usd": ars_to_usd(flujo_financiero, rate),
                "flujo_neto_ars": round(flujo_neto, 2),
                "flujo_neto_usd": ars_to_usd(flujo_neto, rate),
                "saldo_caja_ars": round(saldo_caja, 2),
                "saldo_caja_usd": ars_to_usd(saldo_caja, rate),
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


def split_exact(total: float, weights) -> list[float]:
    """Reparte total según pesos, redondeado a 2 decimales; el último absorbe el residuo (suma exacta)."""
    w = np.array(weights, dtype=float); w = w / w.sum()
    parts = [round(total * x, 2) for x in w[:-1]]
    parts.append(round(total - sum(parts), 2))
    return parts


def generate_ventas(rng: random.Random, months: list[pd.Timestamp], rate: float, pl: pd.DataFrame) -> None:
    monthly = []
    by_product = []
    by_channel = []
    by_region = []
    client_rows = []

    weights_ch = [0.38, 0.28, 0.18, 0.16]
    weights_reg = [0.22, 0.18, 0.14, 0.16, 0.15, 0.15]

    for i, m in enumerate(months):
        # Ventas netas = Ingresos del estado de resultados (misma fuente)
        total = float(pl.iloc[i]["ingresos_ars"])
        prod_shares = [rng.random() + 0.5 for _ in PRODUCTS]
        prod_amts = split_exact(total, prod_shares)
        prod_units = [int(a / rng.uniform(800, 2500)) for a in prod_amts]
        units_total = sum(prod_units)
        monthly.append(
            {
                "empresa": COMPANY,
                "mes": m.strftime("%Y-%m"),
                "ventas_netas_ars": round(total, 2),
                "ventas_netas_usd": ars_to_usd(total, rate),
                "unidades": units_total,
                "ticket_promedio_ars": round(total / units_total, 2),
            }
        )

        for (sku, name), amt, u in zip(PRODUCTS, prod_amts, prod_units):
            by_product.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "sku": sku,
                    "producto": name,
                    "ventas_ars": round(amt, 2),
                    "ventas_usd": ars_to_usd(amt, rate),
                    "unidades": u,
                }
            )

        ch_amts = split_exact(total, [w * (1 + rng.uniform(-0.08, 0.08)) for w in weights_ch])
        for ch, amt in zip(CHANNELS, ch_amts):
            by_channel.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "canal": ch,
                    "ventas_ars": round(amt, 2),
                    "ventas_usd": ars_to_usd(amt, rate),
                }
            )

        reg_amts = split_exact(total, [w * (1 + rng.uniform(-0.1, 0.1)) for w in weights_reg])
        for reg, amt in zip(REGIONS, reg_amts):
            by_region.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "region": reg,
                    "ventas_ars": round(amt, 2),
                    "ventas_usd": ars_to_usd(amt, rate),
                }
            )

    # Top 10 clientes = ~35% de los ingresos de los últimos 12 meses (subconjunto consistente)
    ltm = float(pl["ingresos_ars"].iloc[-12:].sum())
    cli_amts = split_exact(ltm * 0.35, [rng.uniform(1, 4) for _ in CLIENTS])
    for rank, ((cid, cname), base) in enumerate(zip(CLIENTS, cli_amts), start=1):
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


def generate_costos(rng: random.Random, months: list[pd.Timestamp], rate: float, pl: pd.DataFrame, units: pd.DataFrame) -> None:
    fv_rows = []
    cc_rows = []
    unit_rows = []
    var_rows = []

    for i, m in enumerate(months):
        # Costo total = Costo de ventas + Gastos operativos del P&L (excluye depreciación)
        row = pl.iloc[i]
        mes = m.strftime("%Y-%m")
        u_m = units[units["mes"] == mes]
        vol = int(u_m["unidades"].sum())
        total = round(float(row["costo_ventas_ars"]) + float(row["gastos_operativos_ars"]), 2)
        fixed = round(22_000_000 * (1 + 0.01 * i), 2)
        variable = round(total - fixed, 2)
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
        cc_amts = split_exact(total, [sh * (1 + rng.uniform(-0.05, 0.05)) for sh in shares])
        for (cc_id, cc_name), amt in zip(COST_CENTERS, cc_amts):
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

        # Costo de ventas asignado por SKU (suma exacta = costo de ventas del P&L)
        cogs_parts = split_exact(float(row["costo_ventas_ars"]), [float(x) * rng.uniform(0.9, 1.1) for x in u_m["unidades"]])
        for (sku, name), cogs_p, u in zip(PRODUCTS, cogs_parts, u_m["unidades"]):
            uc = cogs_p / int(u)
            unit_rows.append(
                {
                    "empresa": COMPANY,
                    "mes": m.strftime("%Y-%m"),
                    "sku": sku,
                    "producto": name,
                    "costo_unitario_ars": round(uc, 2),
                    "costo_unitario_usd": ars_to_usd(uc, rate),
                    "unidades": int(u),
                    "costo_ventas_ars": cogs_p,
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
    pl = pd.read_csv(DATA_DIR / "financiero_estado_resultados.csv")
    generate_ventas(rng, months, rate, pl)
    units = pd.read_csv(DATA_DIR / "ventas_por_producto.csv")
    generate_costos(rng, months, rate, pl, units)

    print(f"Datos generados en {DATA_DIR} ({MONTHS} meses).")
    print(
        f"Cotización: {rate} ARS/USD ({cfg['fecha']}) — "
        f"{'respaldo' if cfg.get('fallback') else 'BCRA'}"
    )


if __name__ == "__main__":
    main()
