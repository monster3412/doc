import pandas as pd
import numpy as np
from datetime import datetime

workshops = ['Цех 1', 'Цех 2', 'Цех 3', 'Цех 4', 'Цех 5']
products = ['Деталь А', 'Узел Б', 'Корпус В']
months = pd.date_range('2025-01-01', '2025-12-01', freq='MS')

# 1. Генерация планов
plans = []
for w in workshops:
    for m in months:
        for p in products:
            plans.append({
                'workshop': w,
                'date': m.strftime('%Y-%m'),
                'product': p,
                'plan_qty': np.random.randint(80, 120)
            })
pd.DataFrame(plans).to_excel('plans.xlsx', index=False)

# 2. Генерация факта (±15% от плана + редкие пропуски)
facts = []
for w in workshops:
    for m in months:
        for p in products:
            plan = np.random.randint(80, 120)
            fact = max(0, int(plan * np.random.uniform(0.85, 1.15)))
            if np.random.random() > 0.95: fact = 0  # имитация простоя
            facts.append({
                'workshop': w,
                'date': m.strftime('%Y-%m'),
                'product': p,
                'fact_qty': fact
            })
pd.DataFrame(facts).to_csv('workshop_production_data.csv', index=False)
print("✅ Файлы созданы: plans.xlsx, workshop_production_data.csv")