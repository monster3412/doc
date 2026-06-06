# === ФАЙЛ: generate_data.py ===
"""Генерация синтетических данных для демонстрации приложения."""

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def generate_data() -> None:
    """Создаёт плановые и фактические данные в папке data/."""
    workshops = ["Цех 1", "Цех 2", "Цех 3", "Цех 4", "Цех 5"]
    products = ["Деталь А", "Узел Б", "Корпус В"]
    months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")

    np.random.seed(7)

    plans = []
    for workshop in workshops:
        for month in months:
            for product in products:
                plans.append(
                    {
                        "workshop": workshop,
                        "date": month.strftime("%Y-%m"),
                        "product": product,
                        "plan_qty": int(np.random.randint(80, 121)),
                    }
                )

    plan_df = pd.DataFrame(plans)
    plan_df.to_excel(DATA_DIR / "plans.xlsx", index=False)

    facts = []
    for workshop in workshops:
        for month in months:
            for product in products:
                plan_qty = int(np.random.randint(80, 121))
                fact_qty = max(0, int(plan_qty * np.random.uniform(0.85, 1.15)))
                if np.random.random() > 0.95:
                    fact_qty = 0
                facts.append(
                    {
                        "workshop": workshop,
                        "date": month.strftime("%Y-%m"),
                        "product": product,
                        "fact_qty": fact_qty,
                    }
                )

    fact_df = pd.DataFrame(facts)
    fact_df.to_csv(DATA_DIR / "workshop_production_data.csv", index=False)

    print("✅ Файлы созданы:")
    print(f"   - {DATA_DIR / 'plans.xlsx'}")
    print(f"   - {DATA_DIR / 'workshop_production_data.csv'}")


if __name__ == "__main__":
    generate_data()
