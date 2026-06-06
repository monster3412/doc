# === ФАЙЛ: src/exporter.py ===
"""Экспорт отчётов в Excel, PDF и HTML."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.drawing.image import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import Image as RLImage
from reportlab.platypus import Image as RLImageElement
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _save_figure(fig, file_path: Path) -> None:
    """Сохраняет график в PNG-файл."""
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _safe_output_name(workshop: str, start: str, end: str, ext: str) -> str:
    """Возвращает корректное имя файла для экспорта."""
    safe_workshop = "all" if workshop in ("", "Все") else workshop.replace(" ", "_")
    return f"Отчёт_по_цеху_{safe_workshop}_{start}_{end}.{ext}"


def export_excel(df: pd.DataFrame, fig, path: str | Path) -> None:
    """Экспортирует отчёт в Excel с графиком."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(file_path, index=False)
    workbook = load_workbook(file_path)
    sheet = workbook.active
    sheet.freeze_panes = "A2"

    for column in sheet.columns:
        max_length = max(len(str(cell.value)) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 30)

    sheet["A1"].font = Font(bold=True)
    image_path = file_path.with_suffix(".png")
    _save_figure(fig, image_path)
    img = Image(image_path)
    sheet.add_image(img, "G2")
    workbook.save(file_path)


def export_pdf(df: pd.DataFrame, fig, path: str | Path) -> None:
    """Экспортирует отчёт в PDF."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    image_path = file_path.with_suffix(".png")
    _save_figure(fig, image_path)

    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph("WorkshopReport", styles["Title"]), Spacer(1, 12)]

    table_data = [list(df.columns)] + df.astype(str).values.tolist()
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(RLImageElement(str(image_path), width=450, height=180))
    doc.build(story)


def export_html(df: pd.DataFrame, fig, path: str | Path) -> None:
    """Экспортирует отчёт в HTML."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    image_path = file_path.with_suffix(".png")
    _save_figure(fig, image_path)

    html_table = df.to_html(index=False, border=1)
    html_content = f"""
    <html>
      <head>
        <meta charset=\"utf-8\" />
        <title>WorkshopReport</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 20px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; }}
          th {{ background: #2563eb; color: white; }}
        </style>
      </head>
      <body>
        <h1>WorkshopReport</h1>
        {html_table}
        <h2>График</h2>
        <img src=\"{image_path.name}\" alt=\"graph\" />
      </body>
    </html>
    """
    file_path.write_text(html_content, encoding="utf-8")
