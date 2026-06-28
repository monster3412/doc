try:
    from workshop_report.src import loader
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from src import loader

p = loader._locate_file('data/plans.xlsx')
print('located:', p)
try:
    df = loader.load_plans('data/plans.xlsx')
    print('loaded rows:', len(df))
    print('cols:', list(df.columns)[:5])
except Exception as e:
    print('error:', e)
