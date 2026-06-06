# === ФАЙЛ: src/loader.py ===
"""Загрузка, валидация и кеширование данных для отчётов."""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REQUIRED_PLAN_COLUMNS = {"workshop", "date", "product", "plan_qty"}
REQUIRED_FACT_COLUMNS = {"workshop", "date", "product", "fact_qty"}

_CACHE: Dict[str, pd.DataFrame] = {}


def _validate_frame(df: pd.DataFrame, required_columns: set[str], source_name: str) -> pd.DataFrame:
    """Проверяет обязательные столбцы и типы данных."""
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(f"{source_name}: отсутствуют столбцы: {', '.join(missing)}")

    df = df.copy()
    df["workshop"] = df["workshop"].astype(str).str.strip()
    df["product"] = df["product"].astype(str).str.strip()
    df["date"] = df["date"].astype(str).str.strip()

    try:
        pd.to_datetime(df["date"], format="%Y-%m", errors="raise")
    except ValueError as exc:
        raise ValueError("Дата должна быть в формате YYYY-MM") from exc

    if "plan_qty" in df.columns:
        df["plan_qty"] = pd.to_numeric(df["plan_qty"], errors="raise").astype(int)
    if "fact_qty" in df.columns:
        df["fact_qty"] = pd.to_numeric(df["fact_qty"], errors="raise").astype(int)

    return df


def load_plans(path: str | Path) -> pd.DataFrame:
    """Загружает и валидирует плановые данные из XLSX."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    df = pd.read_excel(file_path)
    validated = _validate_frame(df, REQUIRED_PLAN_COLUMNS, "plans.xlsx")
    _CACHE["plans"] = validated
    return validated


def load_facts(path: str | Path) -> pd.DataFrame:
    """Загружает и валидирует фактические данные из CSV."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    df = pd.read_csv(file_path)
    validated = _validate_frame(df, REQUIRED_FACT_COLUMNS, "workshop_production_data.csv")
    _CACHE["facts"] = validated
    return validated


def get_cached_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Возвращает кэшированные DataFrame, если они были загружены."""
    if "plans" not in _CACHE or "facts" not in _CACHE:
        raise ValueError("Данные ещё не загружены. Сначала вызовите load_plans() и load_facts().")
    return _CACHE["plans"].copy(), _CACHE["facts"].copy()
