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

    # use outer join so rows with only plan OR only fact are preserved
    merged = pd.merge(
        plan_work[["workshop", "date", "product", "plan_qty"]],
        fact_work[["workshop", "date", "product", "fact_qty"]],
        on=["workshop", "date", "product"],
        how="outer",
        suffixes=("_plan", "_fact"),
    )

    if merged.empty:
        return pd.DataFrame(columns=["workshop", "date", "product", "plan_qty", "fact_qty", "deviation", "completion_pct"])

    # fill missing numeric values with 0 for arithmetic, but keep plan==0 to mark completion_pct as None
    merged["plan_qty"] = pd.to_numeric(merged.get("plan_qty", 0)).fillna(0).astype(int)
    merged["fact_qty"] = pd.to_numeric(merged.get("fact_qty", 0)).fillna(0).astype(int)

    merged["deviation"] = merged["fact_qty"] - merged["plan_qty"]

    def _pct(row):
        if row["plan_qty"] == 0:
            return None
        return round((row["fact_qty"] / row["plan_qty"] * 100), 1)

    merged["completion_pct"] = merged.apply(_pct, axis=1)

    result = merged[["workshop", "date", "product", "plan_qty", "fact_qty", "deviation", "completion_pct"]].copy()
    result = result.sort_values(["date", "product"]).reset_index(drop=True)
    return result


def calculate_energy_intensity(df: pd.DataFrame) -> float:
    """Энергоёмкость: кВт·ч на единицу продукции = sum(fact_energy) / sum(fact_qty)"""
    if df is None or df.empty:
        return 0.0
    if 'fact_energy' not in df.columns or 'fact_qty' not in df.columns:
        return 0.0
    total_energy = df['fact_energy'].sum()
    total_qty = df['fact_qty'].sum()
    if total_qty == 0:
        return 0.0
    return float(total_energy / total_qty)


def calculate_time_intensity(df: pd.DataFrame) -> float:
    """Трудоёмкость: часов на единицу продукции = sum(fact_time) / sum(fact_qty)"""
    if df is None or df.empty:
        return 0.0
    if 'fact_time' not in df.columns or 'fact_qty' not in df.columns:
        return 0.0
    total_time = df['fact_time'].sum()
    total_qty = df['fact_qty'].sum()
    if total_qty == 0:
        return 0.0
    return float(total_time / total_qty)


def calculate_energy_deviation(plan_df: pd.DataFrame, fact_df: pd.DataFrame) -> float:
    """Отклонение по энергии: sum(fact_energy) - sum(plan_energy)"""
    if plan_df is None or fact_df is None:
        return 0.0
    if 'fact_energy' not in fact_df.columns or 'plan_energy' not in plan_df.columns:
        return 0.0
    return float(fact_df['fact_energy'].sum() - plan_df['plan_energy'].sum())


def calculate_time_utilization(plan_df: pd.DataFrame, fact_df: pd.DataFrame) -> float:
    """Использование времени: (plan_time.sum() / fact_time.sum()) * 100"""
    if plan_df is None or fact_df is None:
        return 0.0
    if 'plan_time' not in plan_df.columns or 'fact_time' not in fact_df.columns:
        return 0.0
    plan_time = plan_df['plan_time'].sum()
    fact_time = fact_df['fact_time'].sum()
    if fact_time == 0:
        return 0.0
    return float((plan_time / fact_time) * 100.0)


def calculate_energy_intensity_plan(plan_df: pd.DataFrame) -> float:
    """Плановая энергоёмкость: sum(plan_energy) / sum(plan_qty)"""
    if plan_df is None or plan_df.empty:
        return 0.0
    if 'plan_energy' not in plan_df.columns or 'plan_qty' not in plan_df.columns:
        return 0.0
    total_energy = plan_df['plan_energy'].sum()
    total_qty = plan_df['plan_qty'].sum()
    if total_qty == 0:
        return 0.0
    return float(total_energy / total_qty)


def calculate_time_intensity_plan(plan_df: pd.DataFrame) -> float:
    """Плановая трудоёмкость: sum(plan_time) / sum(plan_qty)"""
    if plan_df is None or plan_df.empty:
        return 0.0
    if 'plan_time' not in plan_df.columns or 'plan_qty' not in plan_df.columns:
        return 0.0
    total_time = plan_df['plan_time'].sum()
    total_qty = plan_df['plan_qty'].sum()
    if total_qty == 0:
        return 0.0
    return float(total_time / total_qty)


def calculate_time_deviation(plan_df: pd.DataFrame, fact_df: pd.DataFrame) -> float:
    """Отклонение по времени: sum(fact_time) - sum(plan_time)"""
    if plan_df is None or fact_df is None:
        return 0.0
    if 'plan_time' not in plan_df.columns or 'fact_time' not in fact_df.columns:
        return 0.0
    return float(fact_df['fact_time'].sum() - plan_df['plan_time'].sum())


def build_efficiency_table(
    plan_df: pd.DataFrame,
    fact_df: pd.DataFrame,
    workshop: str | list[str] | tuple[str, ...] | set[str] | None = None,
    start: str | None = None,
    end: str | None = None,
    product: Optional[str] = None,
) -> pd.DataFrame:
    """Формирует таблицу эффективности по цехам с энергией и временем."""
    if plan_df is None or fact_df is None:
        return pd.DataFrame(
            columns=[
                'workshop', 'plan_qty', 'fact_qty', 'plan_energy', 'fact_energy',
                'energy_deviation', 'energy_intensity_plan', 'energy_intensity_fact',
                'plan_time', 'fact_time', 'time_deviation', 'time_intensity_plan',
                'time_intensity_fact', 'time_utilization', 'status'
            ]
        )

    plan_work = plan_df.copy()
    fact_work = fact_df.copy()

    if 'date' in plan_work.columns:
        plan_work['date_dt'] = pd.to_datetime(plan_work['date'], format='%Y-%m', errors='coerce')
    if 'date' in fact_work.columns:
        fact_work['date_dt'] = pd.to_datetime(fact_work['date'], format='%Y-%m', errors='coerce')

    if start:
        start_dt = pd.to_datetime(start, format='%Y-%m')
        plan_work = plan_work[plan_work['date_dt'] >= start_dt]
        fact_work = fact_work[fact_work['date_dt'] >= start_dt]
    if end:
        end_dt = pd.to_datetime(end, format='%Y-%m')
        plan_work = plan_work[plan_work['date_dt'] <= end_dt]
        fact_work = fact_work[fact_work['date_dt'] <= end_dt]

    if workshop and workshop != 'Все':
        if isinstance(workshop, (list, tuple, set)):
            allowed = {item for item in workshop if item}
            if allowed:
                plan_work = plan_work[plan_work['workshop'].isin(allowed)]
                fact_work = fact_work[fact_work['workshop'].isin(allowed)]
        else:
            plan_work = plan_work[plan_work['workshop'] == workshop]
            fact_work = fact_work[fact_work['workshop'] == workshop]

    if product and product != 'Все':
        plan_work = plan_work[plan_work['product'] == product]
        fact_work = fact_work[fact_work['product'] == product]

    # ensure numeric columns exist
    for df, qty_col, energy_col, time_col in (
        (plan_work, 'plan_qty', 'plan_energy', 'plan_time'),
        (fact_work, 'fact_qty', 'fact_energy', 'fact_time'),
    ):
        for col in (qty_col, energy_col, time_col):
            if col not in df.columns:
                df[col] = 0
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    plan_agg = plan_work.groupby('workshop', dropna=False).agg(
        plan_qty=('plan_qty', 'sum'),
        plan_energy=('plan_energy', 'sum'),
        plan_time=('plan_time', 'sum'),
    )
    fact_agg = fact_work.groupby('workshop', dropna=False).agg(
        fact_qty=('fact_qty', 'sum'),
        fact_energy=('fact_energy', 'sum'),
        fact_time=('fact_time', 'sum'),
    )

    merged = pd.merge(
        plan_agg.reset_index(),
        fact_agg.reset_index(),
        on='workshop',
        how='outer',
    ).fillna(0)

    merged['energy_deviation'] = merged['fact_energy'] - merged['plan_energy']
    merged['time_deviation'] = merged['fact_time'] - merged['plan_time']
    merged['energy_intensity_plan'] = merged.apply(
        lambda row: float(row['plan_energy'] / row['plan_qty']) if row['plan_qty'] else 0.0,
        axis=1,
    )
    merged['energy_intensity_fact'] = merged.apply(
        lambda row: float(row['fact_energy'] / row['fact_qty']) if row['fact_qty'] else 0.0,
        axis=1,
    )
    merged['time_intensity_plan'] = merged.apply(
        lambda row: float(row['plan_time'] / row['plan_qty']) if row['plan_qty'] else 0.0,
        axis=1,
    )
    merged['time_intensity_fact'] = merged.apply(
        lambda row: float(row['fact_time'] / row['fact_qty']) if row['fact_qty'] else 0.0,
        axis=1,
    )
    merged['time_utilization'] = merged.apply(
        lambda row: float((row['plan_time'] / row['fact_time']) * 100.0) if row['fact_time'] else 0.0,
        axis=1,
    )

    def _status(row):
        if (row['energy_intensity_fact'] <= row['energy_intensity_plan'] and
                row['time_intensity_fact'] <= row['time_intensity_plan']):
            return 'Эффективен'
        if (row['energy_intensity_fact'] > row['energy_intensity_plan'] and
                row['time_intensity_fact'] > row['time_intensity_plan']):
            return 'Перерасход'
        return 'Норма'

    merged['status'] = merged.apply(_status, axis=1)
    columns = [
        'workshop', 'plan_qty', 'fact_qty', 'plan_energy', 'fact_energy',
        'energy_deviation', 'energy_intensity_plan', 'energy_intensity_fact',
        'plan_time', 'fact_time', 'time_deviation', 'time_intensity_plan',
        'time_intensity_fact', 'time_utilization', 'status'
    ]
    return merged[columns].reset_index(drop=True)
