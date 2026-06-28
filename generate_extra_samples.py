from pathlib import Path
import argparse
import numpy as np
import pandas as pd

DATA_DIR = Path('workshop_report/data')
DATA_DIR.mkdir(exist_ok=True)

# allow custom output filenames via CLI
parser = argparse.ArgumentParser(description='Generate example plan/fact datasets with energy/time columns')
parser.add_argument('--plan-out', type=str, default='plans_extra_variant.xlsx', help='plan output filename (xlsx)')
parser.add_argument('--fact-out', type=str, default='workshop_production_data_extra_variant.csv', help='fact output filename (csv)')
args = parser.parse_args()
PLAN_OUT = args.plan_out
FACT_OUT = args.fact_out

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
                # plan energy (kWh) and plan time (hours) per planned unit
                # per-unit energy between 0.8 and 1.6 kWh, per-unit time between 0.15 and 0.9 hours
                'plan_energy': None,
                'plan_time': None,
            })
plan_df = pd.DataFrame(plans)

# compute energy and time based on plan_qty with small random variation
per_unit_energy_plan = np.random.uniform(0.8, 1.6, size=len(plan_df))
per_unit_time_plan = np.random.uniform(0.15, 0.9, size=len(plan_df))
plan_df['plan_energy'] = (plan_df['plan_qty'] * per_unit_energy_plan).round(2)
plan_df['plan_time'] = (plan_df['plan_qty'] * per_unit_time_plan).round(2)

plan_df.to_excel(DATA_DIR / PLAN_OUT, index=False)

facts = []
for workshop in workshops:
    for month in months:
        for product in products:
            plan_qty = int(np.random.randint(70, 131))
            fact_qty = max(0, int(plan_qty * np.random.uniform(0.82, 1.18)))
            if np.random.random() > 0.94:
                fact_qty = 0
            # simulate fact energy/time using per-unit actual consumption
            per_unit_energy_fact = np.random.uniform(0.75, 1.8)
            per_unit_time_fact = np.random.uniform(0.12, 1.1)
            facts.append({
                'workshop': workshop,
                'date': month.strftime('%Y-%m'),
                'product': product,
                'fact_qty': fact_qty,
                'fact_energy': round(fact_qty * per_unit_energy_fact, 2),
                'fact_time': round(fact_qty * per_unit_time_fact, 2),
            })

fact_df = pd.DataFrame(facts)

# ensure fact columns exist even if some rows have zeros
if 'fact_energy' not in fact_df.columns:
    fact_df['fact_energy'] = 0.0
if 'fact_time' not in fact_df.columns:
    fact_df['fact_time'] = 0.0

fact_df.to_csv(DATA_DIR / FACT_OUT, index=False)

print('Created:')
print(' ', DATA_DIR / PLAN_OUT)
print(' ', DATA_DIR / FACT_OUT)
print('Rows plan=', len(plan_df), 'Rows fact=', len(fact_df))
