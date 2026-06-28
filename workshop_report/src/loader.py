# === ФАЙЛ: src/loader.py ===
"""Загрузка, валидация и кеширование данных для отчётов."""

from pathlib import Path
from typing import Dict, Tuple
import re

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
# Дополнительная папка-источник (sibling) — workshop_report_1/data
FALLBACK_DATA_DIR = Path(__file__).resolve().parents[2] / "workshop_report_1" / "data"
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
    file_path = _locate_file(path, preferred_exts=(".xlsx",))
    if not file_path or not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    df = pd.read_excel(file_path)
    validated = _validate_frame(df, REQUIRED_PLAN_COLUMNS, "plans.xlsx")
    _CACHE["plans"] = validated
    _set_extended_flags(validated, "plans")
    return validated


def load_facts(path: str | Path) -> pd.DataFrame:
    """Загружает и валидирует фактические данные из CSV."""
    file_path = _locate_file(path, preferred_exts=(".csv",))
    if not file_path or not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    df = pd.read_csv(file_path)
    validated = _validate_frame(df, REQUIRED_FACT_COLUMNS, "workshop_production_data.csv")
    _CACHE["facts"] = validated
    _set_extended_flags(validated, "facts")
    return validated


def get_cached_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Возвращает кэшированные DataFrame, если они были загружены."""
    if "plans" not in _CACHE or "facts" not in _CACHE:
        raise ValueError("Данные ещё не загружены. Сначала вызовите load_plans() и load_facts().")
    return _CACHE["plans"].copy(), _CACHE["facts"].copy()


def clear_cache() -> None:
    """Очищает кешированные данные из модуля loader."""
    _CACHE.clear()


def parse_table(path: str | Path) -> list[list]:
    """Парсит CSV/JSON/XLSX в список строк для интерфейса загрузки файлов."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path)
    elif suffix == ".json":
        df = pd.read_json(path)
    else:
        raise ValueError("Поддерживаются только файлы CSV, JSON и XLSX.")

    if df.empty:
        return []

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    col_map = {str(c).strip().lower(): c for c in df.columns}

    required = {"workshop", "date", "product"}
    missing = required.difference(col_map)
    if missing:
        raise ValueError(
            f"Файл должен содержать столбцы: {', '.join(sorted(missing))}"
        )

    plan_col = col_map.get("plan_qty") or col_map.get("plan")
    fact_col = col_map.get("fact_qty") or col_map.get("fact")
    plan_energy_col = col_map.get("plan_energy") or col_map.get("planenergy")
    fact_energy_col = col_map.get("fact_energy") or col_map.get("factenergy")
    plan_time_col = col_map.get("plan_time") or col_map.get("plantime")
    fact_time_col = col_map.get("fact_time") or col_map.get("facttime")

    def _parse_int_column(col_name):
        if col_name is None:
            return pd.Series(0, index=df.index, dtype=int)
        s = df[col_name].astype(str).fillna("")
        s = s.str.replace(" ", "", regex=False).str.replace("\u00A0", "", regex=False)
        s = s.str.replace(r"[^0-9,\.\-]", "", regex=True)
        def normalize_num(value: str) -> str:
            if "." in value and "," in value:
                if value.rfind(",") > value.rfind("."):
                    return value.replace(".", "").replace(",", ".")
                return value.replace(",", "")
            if "," in value:
                parts = value.split(",")
                if len(parts[-1]) in (1, 2):
                    return value.replace(",", ".")
                return "".join(parts)
            return value
        s = s.apply(normalize_num)
        return pd.to_numeric(s, errors="coerce").fillna(0).astype(int)

    def _parse_float_column(col_name):
        if col_name is None:
            return pd.Series(0.0, index=df.index, dtype=float)
        s = df[col_name].astype(str).fillna("")
        s = s.str.replace(" ", "", regex=False).str.replace("\u00A0", "", regex=False)
        s = s.str.replace(r"[^0-9,\.\-]", "", regex=True)
        def normalize_num(value: str) -> str:
            if "." in value and "," in value:
                if value.rfind(",") > value.rfind("."):
                    return value.replace(".", "").replace(",", ".")
                return value.replace(",", "")
            if "," in value:
                parts = value.split(",")
                if len(parts[-1]) in (1, 2):
                    return value.replace(",", ".")
                return "".join(parts)
            return value
        s = s.apply(normalize_num)
        return pd.to_numeric(s, errors="coerce").fillna(0.0).astype(float)

    plan_values = _parse_int_column(plan_col)
    fact_values = _parse_int_column(fact_col)
    plan_energy_values = _parse_float_column(plan_energy_col)
    fact_energy_values = _parse_float_column(fact_energy_col)
    plan_time_values = _parse_float_column(plan_time_col)
    fact_time_values = _parse_float_column(fact_time_col)

    rows: list[list] = []
    for idx, row in df.iterrows():
        rows.append([
            str(row[col_map["workshop"]]).strip(),
            str(row[col_map["date"]]).strip(),
            str(row[col_map["product"]]).strip(),
            int(plan_values.iloc[idx]),
            int(fact_values.iloc[idx]),
            float(plan_energy_values.iloc[idx]),
            float(fact_energy_values.iloc[idx]),
            float(plan_time_values.iloc[idx]),
            float(fact_time_values.iloc[idx]),
        ])

    # cache DataFrame if it looks like a plans or facts dataset (preserve extra cols)
    try:
        # normalize expected column names to lower-case
        lower_cols = {c.lower(): c for c in df.columns}
        if "plan_qty" in lower_cols or "plan" in lower_cols:
            # keep numeric energy/time columns if present
            df_copy = df.copy()
            for col in ("plan_qty", "plan_energy", "plan_time"):
                if col in df_copy.columns:
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0)
            _CACHE["plans"] = df_copy
            _set_extended_flags(df_copy, "plans")
        if "fact_qty" in lower_cols or "fact" in lower_cols:
            df_copy = df.copy()
            for col in ("fact_qty", "fact_energy", "fact_time"):
                if col in df_copy.columns:
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0)
            _CACHE["facts"] = df_copy
            _set_extended_flags(df_copy, "facts")
    except Exception:
        pass

    return rows


def _set_extended_flags(df: pd.DataFrame, source_name: str) -> None:
    """Сохраняет флаги наличия расширенных колонок в кеше loader'а."""
    if source_name == "plans":
        _CACHE["extended_plans"] = any(
            col in df.columns for col in ("plan_energy", "plan_time")
        )
    elif source_name == "facts":
        _CACHE["extended_facts"] = any(
            col in df.columns for col in ("fact_energy", "fact_time")
        )


def _locate_file(path: str | Path, preferred_exts: tuple[str, ...] = (".xlsx", ".csv")) -> Path | None:
    """Пытается найти файл по нескольким местам:
    1) как указано (абсолютный или относительный),
    2) относительно `DATA_DIR`,
    3) в `FALLBACK_DATA_DIR`,
    4) относительно текущей рабочей директории.
    Возвращает Path либо None.
    """
    p = Path(path)
    if p.exists():
        return p

    for base in (DATA_DIR, FALLBACK_DATA_DIR, Path.cwd()):
        candidate = base / p
        if candidate.exists():
            return candidate

    return None
