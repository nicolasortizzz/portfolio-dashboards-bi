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
