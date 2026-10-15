#!/usr/bin/env python3
"""Ejecuta el pipeline completo: datos → Excel → imágenes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"


def run(script: str) -> None:
    path = SCRIPTS / script
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable, str(path)], check=True, cwd=str(SCRIPTS))


def main() -> None:
    run("generate_data.py")
    run("check_reconciliation.py")
    run("build_excel.py")
    run("render_dashboards.py")
    print("\nPipeline completado.")


if __name__ == "__main__":
    main()
