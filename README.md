# Economista | Dashboards en Power BI y Excel | Reportes financieros automatizados para pymes

Portfolio de **Business Intelligence** con tres tableros de ejemplo para una pyme argentina ficticia (**NovaCampo Alimentos S.A.**). El objetivo es mostrar automatización de reportes financieros y comerciales en **Excel** y visualizaciones listas para **Power BI**, a partir de los mismos archivos CSV.

> **Aviso importante:** todos los nombres de empresa, clientes, montos y series temporales son **enteramente ficticios** y se generan con un generador aleatorio con semilla fija (`SEED=42`). No representan operaciones reales ni datos de terceros.

## Tipo de cambio ARS/USD

Las columnas en dólares se calculan con el tipo de cambio documentado en `config/exchange_rate.json`:

| Campo | Valor |
| --- | --- |
| **Cotización** | 1514,5655 ARS por USD |
| **Fecha** | 2026-10-14 |
| **Tipo** | Tipo de cambio mayorista de referencia (Comunicación A 3500) |
| **Fuente** | API BCRA Estadísticas Monetarias v4.0 — variable 5 ([bcra.gob.ar](https://www.bcra.gob.ar/)) |

Si la API del BCRA no está disponible al ejecutar `generate_data.py`, se usa una tasa de respaldo fija documentada en el script y en el JSON (`fallback: true`).

Conversión reutilizable: módulo `scripts/fx.py` (`ars_to_usd`, `usd_to_ars`, `load_exchange_config`).

## Cómo regenerar todo

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py
```

O con Make:

```bash
make all
# o paso a paso: make data excel images
```

**Salidas:**

- `data/*.csv` — 24 meses de series ficticias
- `excel/dashboard_*.xlsx` — libros con KPIs, tablas formateadas y gráficos nativos de Excel
- `images/dashboard_*.png` — vistas estilo dashboard (matplotlib)

Un archivo **Power BI (.pbix)** puede armarse importando los CSV de `data/` y replicando las mismas métricas y relaciones por mes, producto, canal y centro de costo.

## Stack

- **Python 3.11+** — pandas, numpy, requests, openpyxl, matplotlib
- **Excel** — tablas con formatos ARS/USD, paneles congelados y gráficos nativos
- **Power BI** — mismo modelo de datos desde CSV (no incluido en el repo; flujo documentado arriba)

---

## 1. Dashboard Financiero

Estado de resultados (P&amp;L), flujo de caja y presupuesto vs. real.

![Dashboard Financiero](images/dashboard_financiero.png)

**KPIs destacados (último mes de la serie ficticia):**

- **Ingresos** — ventas netas mensuales en ARS y USD derivado.
- **EBITDA** — margen operativo antes de depreciación e impuestos.
- **Resultado neto** — cierre después de resultado financiero e impuesto simulado.
- **Flujo de caja neto** — operativo + inversiones + financiero.
- **Presupuesto vs. real** — desvío por concepto (ingresos, costos, gastos, EBITDA).

Archivos: `data/financiero_*.csv` · Excel: `excel/dashboard_financiero.xlsx`

---

## 2. Dashboard Ventas

Ventas por mes, producto, canal, región y ranking de clientes (nombres ficticios).

![Dashboard Ventas](images/dashboard_ventas.png)

**KPIs destacados:**

- **Ventas del mes** y **acumulado 24 meses** en ARS.
- **Unidades** vendidas y ticket promedio simulado.
- **Mix por canal** — mayorista, retail, e-commerce y venta directa.
- **Regiones** — CABA, GBA y interior.
- **Top clientes** — p. ej. *Supermercados Don Horacio S.A.*, *Distribuidora La Ribera S.R.L.* (ficticios).

Archivos: `data/ventas_*.csv` · Excel: `excel/dashboard_ventas.xlsx`

---

## 3. Dashboard Costos

Costos fijos y variables, por centro de costo, costo unitario y variaciones vs. estándar.

![Dashboard Costos](images/dashboard_costos.png)

**KPIs destacados:**

- **Costo total** del mes y desglose **fijo / variable**.
- **Centros de costo** — producción, logística, comercial y administración.
- **Costo unitario** por SKU ficticio.
- **Variación** real vs. costo estándar y evolución del costo por unidad producida.

Archivos: `data/costos_*.csv` · Excel: `excel/dashboard_costos.xlsx`

---

## Estructura del repositorio

```
├── config/exchange_rate.json
├── data/
├── excel/
├── images/
├── scripts/
│   ├── fx.py
│   ├── generate_data.py
│   ├── build_excel.py
│   └── render_dashboards.py
├── run_all.py
├── Makefile
└── requirements.txt
```

## Contacto

- GitHub: [nicolasortizzz](https://github.com/nicolasortizzz)
- LinkedIn: [nicolas-ortizzz](https://www.linkedin.com/in/nicolas-ortizzz/)
