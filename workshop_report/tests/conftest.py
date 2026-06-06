# === ФАЙЛ: tests/conftest.py ===
"""Настройка пути для pytest."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
