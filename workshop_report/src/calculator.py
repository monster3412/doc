# === ФАЙЛ: src/calculator.py ===
"""Расчёт метрик план/факт и фильтрация отчётов."""

from typing import Optional

import pandas as pd


def calculate_metrics(
    plan_df: pd.DataFrame,
    fact_df: pd.DataFrame,
    workshop: str | list[str] | tuple[str, ...] | set[str] | None,
    start: str,
    end: str,
    product: Optional[str] = None,
) -> pd.DataFrame:
    """Строит агрегированный отчёт по плану и факту."""
    plan_work = plan_df.copy()
    fact_work = fact_df.copy()

    plan_work["date_dt"] = pd.to_datetime(plan_work["date"], format="%Y-%m")
    fact_work["date_dt"] = pd.to_datetime(fact_work["date"], format="%Y-%m")

    start_dt = pd.to_datetime(start, format="%Y-%m")
    end_dt = pd.to_datetime(end, format="%Y-%m")

    if start_dt > end_dt:
        raise ValueError("Начальная дата не может быть позже конечной.")

    if workshop and workshop != "Все":
        if isinstance(workshop, (list, tuple, set)):
            selected = {item for item in workshop if item}
            if selected:
                plan_work = plan_work[plan_work["workshop"].isin(selected)]
                fact_work = fact_work[fact_work["workshop"].isin(selected)]
        else:
            plan_work = plan_work[plan_work["workshop"] == workshop]
            fact_work = fact_work[fact_work["workshop"] == workshop]

    if product and product != "Все":
        plan_work = plan_work[plan_work["product"] == product]
        fact_work = fact_work[fact_work["product"] == product]

    plan_work = plan_work[(plan_work["date_dt"] >= start_dt) & (plan_work["date_dt"] <= end_dt)]
    fact_work = fact_work[(fact_work["date_dt"] >= start_dt) & (fact_work["date_dt"] <= end_dt)]

    merged = pd.merge(
        plan_work[["workshop", "date", "product", "plan_qty"]],
        fact_work[["workshop", "date", "product", "fact_qty"]],
        on=["workshop", "date", "product"],
        how="inner",
        suffixes=("_plan", "_fact"),
    )

    if merged.empty:
        return pd.DataFrame(columns=["workshop", "date", "product", "plan_qty", "fact_qty", "deviation", "completion_pct"])

    merged["deviation"] = merged["fact_qty"] - merged["plan_qty"]
    merged["completion_pct"] = merged.apply(
        lambda row: 0.0 if row["plan_qty"] == 0 else round((row["fact_qty"] / row["plan_qty"] * 100), 1),
        axis=1,
    )

    result = merged[["workshop", "date", "product", "plan_qty", "fact_qty", "deviation", "completion_pct"]].copy()
    result = result.sort_values(["date", "product"]).reset_index(drop=True)
    return result
