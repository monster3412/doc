from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path('workshop_report/data')
DATA_DIR.mkdir(exist_ok=True)

workshops = ['Цех Alpha', 'Цех Beta', 'Цех Gamma', 'Цех Delta', 'Цех Epsilon', 'Цех Zeta']
products = ['Деталь A', 'Узел B', 'Корпус C', 'Модуль D', 'Рама E', 'Кронштейн F', 'Шток G', 'Плата H']
months = pd.date_range('2025-01-01', '2025-12-01', freq='MS')

np.random.seed(42)
plans = []
for workshop in workshops:
    for month in months:
        for product in products:
            plans.append({
                'workshop': workshop,
                'date': month.strftime('%Y-%m'),
                'product': product,
                'plan_qty': int(np.random.randint(70, 131)),
            })
plan_df = pd.DataFrame(plans)
plan_df.to_excel(DATA_DIR / 'plans_extra_variant.xlsx', index=False)

facts = []
for workshop in workshops:
    for month in months:
        for product in products:
            plan_qty = int(np.random.randint(70, 131))
            fact_qty = max(0, int(plan_qty * np.random.uniform(0.82, 1.18)))
            if np.random.random() > 0.94:
                fact_qty = 0
            facts.append({
                'workshop': workshop,
                'date': month.strftime('%Y-%m'),
                'product': product,
                'fact_qty': fact_qty,
            })

fact_df = pd.DataFrame(facts)
fact_df.to_csv(DATA_DIR / 'workshop_production_data_extra_variant.csv', index=False)

print('Created:')
print(' ', DATA_DIR / 'plans_extra_variant.xlsx')
print(' ', DATA_DIR / 'workshop_production_data_extra_variant.csv')
print('Rows plan=', len(plan_df), 'Rows fact=', len(fact_df))
