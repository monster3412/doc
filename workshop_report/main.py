# === ФАЙЛ: main.py ===
"""Точка входа приложения WorkshopReport."""

try:
    from workshop_report.src.ui import ReportApp
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from src.ui import ReportApp


def main() -> None:
    """Запуск главного окна."""
    app = ReportApp()
    app.mainloop()


if __name__ == "__main__":
    main()
