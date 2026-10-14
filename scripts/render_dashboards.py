#!/usr/bin/env python3
"""Renderiza dashboards estilo portfolio en PNG (matplotlib)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMAGES = ROOT / "images"

THEME = {
    "bg": "#F4F6F8",
    "card": "#FFFFFF",
    "primary": "#1F4E79",
    "accent": "#2E75B6",
    "success": "#548235",
    "warning": "#C55A11",
    "text": "#2B2B2B",
    "muted": "#7A7A7A",
    "grid": "#E0E0E0",
}


def fmt_ars(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:,.0f}"


def kpi_card(fig, spec, title: str, value: str, subtitle: str = "") -> None:
    ax = fig.add_axes(spec)
    ax.set_facecolor(THEME["card"])
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(0.06, 0.72, title, fontsize=10, color=THEME["muted"], transform=ax.transAxes)
    ax.text(0.06, 0.38, value, fontsize=16, fontweight="bold", color=THEME["primary"], transform=ax.transAxes)
    if subtitle:
        ax.text(0.06, 0.12, subtitle, fontsize=9, color=THEME["text"], transform=ax.transAxes)


def style_ax(ax, title: str) -> None:
    ax.set_title(title, fontsize=11, fontweight="bold", color=THEME["primary"], loc="left", pad=12)
    ax.tick_params(colors=THEME["text"], labelsize=8)
    ax.grid(axis="y", color=THEME["grid"], linestyle="--", linewidth=0.6, alpha=0.8)
    ax.set_facecolor(THEME["card"])
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)


def save_dashboard(fig, path: Path) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=THEME["bg"])
    plt.close(fig)
    print(f"PNG generado: {path}")


def render_financiero() -> Path:
    pl = pd.read_csv(DATA / "financiero_estado_resultados.csv")
    cf = pd.read_csv(DATA / "financiero_flujo_caja.csv")
    bvr = pd.read_csv(DATA / "financiero_presupuesto_vs_real.csv")

    last = pl.iloc[-1]
    fig = plt.figure(figsize=(14, 9), facecolor=THEME["bg"])
    fig.suptitle(
        "Dashboard Financiero — NovaCampo Alimentos S.A. (datos ficticios)",
        fontsize=14,
        fontweight="bold",
        color=THEME["primary"],
        x=0.05,
        y=0.97,
        ha="left",
    )

    kpi_card(fig, [0.05, 0.82, 0.2, 0.1], "Ingresos (últ. mes)", fmt_ars(last["ingresos_ars"]))
    kpi_card(fig, [0.27, 0.82, 0.2, 0.1], "EBITDA", fmt_ars(last["ebitda_ars"]), f"Margen {last['ebitda_ars']/last['ingresos_ars']*100:.1f}%")
    kpi_card(fig, [0.49, 0.82, 0.2, 0.1], "Resultado neto", fmt_ars(last["resultado_neto_ars"]))
    kpi_card(fig, [0.71, 0.82, 0.24, 0.1], "Flujo neto", fmt_ars(cf.iloc[-1]["flujo_neto_ars"]), cf.iloc[-1]["mes"])

    ax1 = fig.add_axes([0.06, 0.48, 0.42, 0.28])
    style_ax(ax1, "Ingresos y EBITDA (ARS)")
    ax1.plot(pl["mes"], pl["ingresos_ars"], color=THEME["accent"], marker="o", markersize=3, label="Ingresos")
    ax1.plot(pl["mes"], pl["ebitda_ars"], color=THEME["success"], marker="o", markersize=3, label="EBITDA")
    ax1.legend(fontsize=8, frameon=False)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

    ax2 = fig.add_axes([0.54, 0.48, 0.4, 0.28])
    style_ax(ax2, "Flujo de caja neto (ARS)")
    colors = [THEME["success"] if v >= 0 else THEME["warning"] for v in cf["flujo_neto_ars"]]
    ax2.bar(cf["mes"], cf["flujo_neto_ars"], color=colors, width=0.7)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")

    ax3 = fig.add_axes([0.06, 0.1, 0.42, 0.28])
    style_ax(ax3, "Margen neto %")
    margin = pl["resultado_neto_ars"] / pl["ingresos_ars"] * 100
    ax3.fill_between(range(len(margin)), margin, color=THEME["accent"], alpha=0.25)
    ax3.plot(pl["mes"], margin, color=THEME["primary"], linewidth=2)
    ax3.set_ylabel("%")
    plt.setp(ax3.get_xticklabels(), rotation=45, ha="right")

    last_m = pl.iloc[-1]["mes"]
    b_last = bvr[(bvr["mes"] == last_m) & (bvr["concepto"].isin(["Ingresos", "EBITDA", "Gastos operativos"]))]
    ax4 = fig.add_axes([0.54, 0.1, 0.4, 0.28])
    style_ax(ax4, f"Presupuesto vs Real — {last_m} (ARS)")
    x = np.arange(len(b_last))
    w = 0.35
    ax4.bar(x - w / 2, b_last["presupuesto_ars"], width=w, label="Presupuesto", color=THEME["muted"])
    ax4.bar(x + w / 2, b_last["real_ars"], width=w, label="Real", color=THEME["accent"])
    ax4.set_xticks(x)
    ax4.set_xticklabels(b_last["concepto"], fontsize=8)
    ax4.legend(fontsize=8, frameon=False)
    ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))

    path = IMAGES / "dashboard_financiero.png"
    save_dashboard(fig, path)
    return path


def render_ventas() -> Path:
    mensual = pd.read_csv(DATA / "ventas_mensual.csv")
    canal = pd.read_csv(DATA / "ventas_por_canal.csv")
    region = pd.read_csv(DATA / "ventas_por_region.csv")
    prod = pd.read_csv(DATA / "ventas_por_producto.csv")
    clientes = pd.read_csv(DATA / "ventas_top_clientes.csv")

    last_m = mensual.iloc[-1]["mes"]
    fig = plt.figure(figsize=(14, 9), facecolor=THEME["bg"])
    fig.suptitle(
        "Dashboard Ventas — NovaCampo Alimentos S.A. (datos ficticios)",
        fontsize=14,
        fontweight="bold",
        color=THEME["primary"],
        x=0.05,
        y=0.97,
        ha="left",
    )

    kpi_card(fig, [0.05, 0.82, 0.2, 0.1], "Ventas últ. mes", fmt_ars(mensual.iloc[-1]["ventas_netas_ars"]))
    kpi_card(fig, [0.27, 0.82, 0.2, 0.1], "Acum. 24 meses", fmt_ars(mensual["ventas_netas_ars"].sum()))
    kpi_card(fig, [0.49, 0.82, 0.2, 0.1], "Unidades", f"{mensual.iloc[-1]['unidades']:,}")
    kpi_card(fig, [0.71, 0.82, 0.24, 0.1], "Top cliente", clientes.iloc[0]["cliente"][:28] + "…", fmt_ars(clientes.iloc[0]["ventas_12m_ars"]))

    ax1 = fig.add_axes([0.06, 0.48, 0.42, 0.28])
    style_ax(ax1, "Ventas netas mensuales (ARS)")
    ax1.plot(mensual["mes"], mensual["ventas_netas_ars"], color=THEME["accent"], linewidth=2, marker="o", markersize=3)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

    c_last = canal[canal["mes"] == last_m]
    ax2 = fig.add_axes([0.54, 0.48, 0.4, 0.28])
    ax2.set_title("Mix por canal", fontsize=11, fontweight="bold", color=THEME["primary"], loc="left")
    ax2.pie(
        c_last["ventas_ars"],
        labels=c_last["canal"],
        autopct="%1.0f%%",
        startangle=90,
        colors=plt.cm.Blues(np.linspace(0.35, 0.85, len(c_last))),
        textprops={"fontsize": 8},
    )

    p_last = prod[prod["mes"] == last_m].groupby("producto", as_index=False)["ventas_ars"].sum().nlargest(5, "ventas_ars")
    ax3 = fig.add_axes([0.06, 0.1, 0.28, 0.28])
    style_ax(ax3, "Top 5 productos (últ. mes)")
    ax3.bar(range(len(p_last)), p_last["ventas_ars"], color=THEME["success"])
    ax3.set_xticks(range(len(p_last)))
    ax3.set_xticklabels([p[:10] + "…" for p in p_last["producto"]], fontsize=7, rotation=30, ha="right")
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))

    r_last = region[region["mes"] == last_m].sort_values("ventas_ars", ascending=True)
    ax4 = fig.add_axes([0.36, 0.1, 0.28, 0.28])
    style_ax(ax4, f"Ventas por región — {last_m}")
    ax4.barh(r_last["region"], r_last["ventas_ars"], color=THEME["accent"])
    ax4.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))

    ax5 = fig.add_axes([0.66, 0.1, 0.28, 0.28])
    style_ax(ax5, "Top 5 clientes (12m ARS)")
    top5 = clientes.head(5).sort_values("ventas_12m_ars", ascending=True)
    ax5.barh(top5["cliente"].str[:18], top5["ventas_12m_ars"], color=THEME["primary"])
    ax5.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))

    path = IMAGES / "dashboard_ventas.png"
    save_dashboard(fig, path)
    return path


def render_costos() -> Path:
    fv = pd.read_csv(DATA / "costos_fijo_variable.csv")
    cc = pd.read_csv(DATA / "costos_por_centro.csv")
    unit = pd.read_csv(DATA / "costos_unitarios.csv")
    var = pd.read_csv(DATA / "costos_variaciones.csv")

    last_m = fv.iloc[-1]["mes"]
    last = fv.iloc[-1]
    fig = plt.figure(figsize=(14, 9), facecolor=THEME["bg"])
    fig.suptitle(
        "Dashboard Costos — NovaCampo Alimentos S.A. (datos ficticios)",
        fontsize=14,
        fontweight="bold",
        color=THEME["primary"],
        x=0.05,
        y=0.97,
        ha="left",
    )

    kpi_card(fig, [0.05, 0.82, 0.2, 0.1], "Costo total", fmt_ars(last["costo_total_ars"]))
    kpi_card(fig, [0.27, 0.82, 0.2, 0.1], "Fijos", fmt_ars(last["costos_fijos_ars"]))
    kpi_card(fig, [0.49, 0.82, 0.2, 0.1], "Variables", fmt_ars(last["costos_variables_ars"]))
    kpi_card(fig, [0.71, 0.82, 0.24, 0.1], "Variación", f"{var.iloc[-1]['variacion_pct']:.2f}%", last_m)

    ax1 = fig.add_axes([0.06, 0.48, 0.42, 0.28])
    style_ax(ax1, "Costos fijos vs variables (ARS)")
    ax1.stackplot(
        range(len(fv)),
        fv["costos_fijos_ars"],
        fv["costos_variables_ars"],
        labels=["Fijos", "Variables"],
        colors=[THEME["primary"], THEME["accent"]],
        alpha=0.85,
    )
    ax1.set_xticks(range(0, len(fv), 4))
    ax1.set_xticklabels(fv["mes"].iloc[::4], rotation=45, ha="right", fontsize=7)
    ax1.legend(loc="upper left", fontsize=8, frameon=False)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_ars(x)))

    cc_last = cc[cc["mes"] == last_m]
    ax2 = fig.add_axes([0.54, 0.48, 0.4, 0.28])
    ax2.set_title("Por centro de costo", fontsize=11, fontweight="bold", color=THEME["primary"], loc="left")
    ax2.pie(
        cc_last["costo_ars"],
        labels=cc_last["centro_costo"],
        autopct="%1.0f%%",
        startangle=140,
        colors=plt.cm.Greens(np.linspace(0.35, 0.85, len(cc_last))),
        textprops={"fontsize": 8},
    )

    u_last = unit[unit["mes"] == last_m]
    ax3 = fig.add_axes([0.06, 0.1, 0.42, 0.28])
    style_ax(ax3, f"Costo unitario por producto — {last_m}")
    ax3.bar(u_last["producto"].str[:10], u_last["costo_unitario_ars"], color=THEME["warning"])
    plt.setp(ax3.get_xticklabels(), rotation=30, ha="right", fontsize=7)
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    ax4 = fig.add_axes([0.54, 0.1, 0.4, 0.28])
    style_ax(ax4, "Variación costo (%) y costo por unidad")
    ax4.plot(var["mes"], var["variacion_pct"], color=THEME["primary"], marker="o", markersize=3, label="Var. %")
    ax4.axhline(0, color=THEME["muted"], linewidth=0.8)
    ax4b = ax4.twinx()
    cpu = fv["costo_total_ars"] / fv["unidades_producidas"]
    ax4b.plot(fv["mes"], cpu, color=THEME["success"], linewidth=2, label="$/unidad")
    ax4.legend(loc="upper left", fontsize=7, frameon=False)
    plt.setp(ax4.get_xticklabels(), rotation=45, ha="right", fontsize=7)

    path = IMAGES / "dashboard_costos.png"
    save_dashboard(fig, path)
    return path


def main() -> None:
    render_financiero()
    render_ventas()
    render_costos()


if __name__ == "__main__":
    main()
