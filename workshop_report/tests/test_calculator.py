# === ФАЙЛ: tests/test_calculator.py ===
"""Тесты для расчёта метрик."""

import pandas as pd

try:
    from workshop_report.src.calculator import calculate_metrics
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.calculator import calculate_metrics


def test_calculate_metrics_correct_values() -> None:
    plan_df = pd.DataFrame(
        [
            {"workshop": "Цех 1", "date": "2025-01", "product": "A", "plan_qty": 100},
        ]
    )
    fact_df = pd.DataFrame(
        [
            {"workshop": "Цех 1", "date": "2025-01", "product": "A", "fact_qty": 120},
        ]
    )

    result = calculate_metrics(plan_df, fact_df, "Цех 1", "2025-01", "2025-01")

    assert not result.empty
    assert result.loc[0, "deviation"] == 20
    assert result.loc[0, "completion_pct"] == 120.0


def test_calculate_metrics_zero_plan_returns_zero_completion() -> None:
    plan_df = pd.DataFrame(
        [{"workshop": "Цех 1", "date": "2025-01", "product": "A", "plan_qty": 0}]
    )
    fact_df = pd.DataFrame(
        [{"workshop": "Цех 1", "date": "2025-01", "product": "A", "fact_qty": 10}]
    )

    result = calculate_metrics(plan_df, fact_df, "Цех 1", "2025-01", "2025-01")

    assert result.loc[0, "completion_pct"] == 0.0


def test_calculate_metrics_filters_by_workshop() -> None:
    plan_df = pd.DataFrame(
        [
            {"workshop": "Цех 1", "date": "2025-01", "product": "A", "plan_qty": 100},
            {"workshop": "Цех 2", "date": "2025-01", "product": "A", "plan_qty": 50},
        ]
    )
    fact_df = pd.DataFrame(
        [
            {"workshop": "Цех 1", "date": "2025-01", "product": "A", "fact_qty": 90},
            {"workshop": "Цех 2", "date": "2025-01", "product": "A", "fact_qty": 40},
        ]
    )

    result = calculate_metrics(plan_df, fact_df, "Цех 1", "2025-01", "2025-01")

    assert len(result) == 1
    assert result.loc[0, "plan_qty"] == 100
    assert result.loc[0, "fact_qty"] == 90


def test_calculate_metrics_filters_by_multiple_workshops() -> None:
    plan_df = pd.DataFrame(
        [
            {"workshop": "Цех 1", "date": "2025-01", "product": "A", "plan_qty": 100},
            {"workshop": "Цех 2", "date": "2025-01", "product": "A", "plan_qty": 50},
            {"workshop": "Цех 3", "date": "2025-01", "product": "A", "plan_qty": 30},
        ]
    )
    fact_df = pd.DataFrame(
        [
            {"workshop": "Цех 1", "date": "2025-01", "product": "A", "fact_qty": 90},
            {"workshop": "Цех 2", "date": "2025-01", "product": "A", "fact_qty": 40},
            {"workshop": "Цех 3", "date": "2025-01", "product": "A", "fact_qty": 20},
        ]
    )

    result = calculate_metrics(plan_df, fact_df, ["Цех 1", "Цех 2"], "2025-01", "2025-01")

    assert len(result) == 2
    assert set(result["product"]) == {"A"}
