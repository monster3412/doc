# === ФАЙЛ: main.py ===
"""Точка входа приложения WorkshopReport."""

from src.ui import ReportApp


def main() -> None:
    """Запуск главного окна."""
    app = ReportApp()
    app.mainloop()


if __name__ == "__main__":
    main()
