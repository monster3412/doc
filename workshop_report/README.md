# WorkshopReport

Учебное десктопное приложение для анализа выполнения планов цехов.

## Запуск
1. python -m venv .venv
2. .\.venv\Scripts\activate
3. pip install -r requirements.txt
4. python generate_data.py
5. python main.py

## Тесты
pytest tests/test_calculator.py

## Сборка
pyinstaller --onefile --windowed --add-data "data;data" main.py
