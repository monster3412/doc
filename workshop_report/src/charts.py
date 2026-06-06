# === ФАЙЛ: src/charts.py ===
"""Генерация графиков для отчёта."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def build_charts(metrics_df: pd.DataFrame):
    """Создаёт Figure с двумя графиками для встраивания в tkinter."""
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), dpi=110)
    fig.patch.set_facecolor("#07111f")

    if metrics_df.empty:
        for ax in axes:
            ax.set_facecolor("#0f172a")
            ax.text(0.5, 0.5, "Нет данных для отображения", ha="center", va="center", color="#e5eefb")
            ax.set_axis_off()
        return fig

    for ax in axes:
        ax.set_facecolor("#0f172a")
        ax.grid(True, axis="y", linestyle="--", linewidth=0.8, alpha=0.35, color="#94a3b8")
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#334155")
        ax.spines["bottom"].set_color("#334155")
        ax.title.set_color("#f8fafc")
        ax.yaxis.label.set_color("#e5eefb")

    product_summary = metrics_df.groupby("product", as_index=False).agg(plan_qty=("plan_qty", "sum"), fact_qty=("fact_qty", "sum"))
    x = np.arange(len(product_summary))
    w = 0.35
    bars1 = axes[0].bar(x - w/2, product_summary["plan_qty"], width=w, label="План", color="#60a5fa", alpha=0.95)
    bars2 = axes[0].bar(x + w/2, product_summary["fact_qty"], width=w, label="Факт", color="#34d399", alpha=0.95)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(product_summary["product"], rotation=15)
    axes[0].set_title("План vs Факт по продукции", loc="left", pad=12)
    axes[0].set_ylabel("Объём")
    axes[0].legend(bbox_to_anchor=(0.5, 1.12), loc='center', ncol=2, frameon=False, labelcolor="#e5eefb")
    # value labels
    for b in bars1 + bars2:
        h = b.get_height()
        axes[0].annotate(f"{int(h):,}".replace(",", " "), xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 6), textcoords="offset points", ha="center", va="bottom", color="#e5eefb", fontsize=9)

    completion_by_date = metrics_df.groupby("date", as_index=False)["completion_pct"].mean().sort_values("date")
    axes[1].plot(completion_by_date["date"], completion_by_date["completion_pct"], marker="o", color="#a78bfa", linewidth=2.4, markersize=8)
    axes[1].axhline(100, color="#94a3b8", linestyle="--", linewidth=1)
    axes[1].set_title("Выполнение плана по месяцам", loc="left", pad=12)
    axes[1].set_ylabel("Выполнение, %")
    axes[1].tick_params(axis="x", rotation=35)
    # point labels
    for x_val, y_val in zip(completion_by_date["date"], completion_by_date["completion_pct"]):
        axes[1].annotate(f"{y_val:.1f}%", xy=(x_val, y_val), xytext=(0, 8), textcoords="offset points", ha="center", color="#e5eefb", fontsize=9)

    fig.tight_layout()
    return fig
