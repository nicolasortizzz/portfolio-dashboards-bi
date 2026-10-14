"""Conversión ARS/USD usando la cotización documentada en config/exchange_rate.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "exchange_rate.json"

FALLBACK_RATE = 1200.0
FALLBACK_DATE = "2025-01-15"
FALLBACK_SOURCE = (
    "Tasa fija de respaldo documentada en el repositorio "
    "(solo si la API del BCRA no está disponible)."
)


def load_exchange_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG
    if cfg_path.is_file():
        with cfg_path.open(encoding="utf-8") as f:
            return json.load(f)
    return {
        "ars_per_usd": FALLBACK_RATE,
        "fecha": FALLBACK_DATE,
        "fuente": FALLBACK_SOURCE,
        "tipo": "Tipo de cambio mayorista de referencia (Comunicación A 3500)",
        "fallback": True,
    }


def ars_to_usd(amount_ars: float, ars_per_usd: float | None = None) -> float:
    rate = ars_per_usd if ars_per_usd is not None else load_exchange_config()["ars_per_usd"]
    return round(amount_ars / rate, 2)


def usd_to_ars(amount_usd: float, ars_per_usd: float | None = None) -> float:
    rate = ars_per_usd if ars_per_usd is not None else load_exchange_config()["ars_per_usd"]
    return round(amount_usd * rate, 2)


def _fmt_decimal_comma(value: float, decimals: int) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_ars_compact(amount_ars: float) -> str:
    """Etiqueta corta en pesos (formato AR): p. ej. ARS 109,2 M."""
    sign = "-" if amount_ars < 0 else ""
    x = abs(amount_ars)
    if x >= 1_000_000:
        return f"{sign}ARS {_fmt_decimal_comma(x / 1_000_000, 1)} M"
    if x >= 1_000:
        return f"{sign}ARS {_fmt_decimal_comma(x / 1_000, 1)} k"
    return f"{sign}ARS {_fmt_decimal_comma(x, 0)}"


def format_usd_compact(amount_usd: float) -> str:
    """Etiqueta corta en USD: p. ej. USD 72,1 k."""
    sign = "-" if amount_usd < 0 else ""
    x = abs(amount_usd)
    if x >= 1_000_000:
        return f"{sign}USD {_fmt_decimal_comma(x / 1_000_000, 1)} M"
    if x >= 1_000:
        return f"{sign}USD {_fmt_decimal_comma(x / 1_000, 1)} k"
    return f"{sign}USD {_fmt_decimal_comma(x, 1)}"


def format_kpi_ars_usd(amount_ars: float, ars_per_usd: float | None = None) -> str:
    rate = ars_per_usd if ars_per_usd is not None else load_exchange_config()["ars_per_usd"]
    usd = amount_ars / rate
    return f"{format_ars_compact(amount_ars)} ({format_usd_compact(usd)})"


def excel_ars_format() -> str:
    return '#.##0,00 "ARS"'


def excel_usd_format() -> str:
    return '#.##0,00 "USD"'
