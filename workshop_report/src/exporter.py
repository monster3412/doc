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

    # write main sheet
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

    # attempt to add 'Эффективность' sheet if extended data available via loader
    try:
        from . import loader as _loader
        plans = _loader._CACHE.get('plans')
        facts = _loader._CACHE.get('facts')
        eff_frame = _build_efficiency_frame(plans, facts)
        if eff_frame is not None:
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                eff_frame.to_excel(writer, sheet_name='Эффективность', index=False)
    except Exception:
        # non-critical
        pass


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
    extra_html = ""
    try:
        from . import loader
        plans = loader._CACHE.get('plans')
        facts = loader._CACHE.get('facts')
        eff_frame = _build_efficiency_frame(plans, facts)
        if eff_frame is not None:
            extra_html = '<h2>Эффективность производства</h2>' + eff_frame.to_html(index=False, float_format=lambda x: f"{x:.2f}")
        else:
            extra_html = '<p>Графики/таблицы эффективности недоступны</p>'
    except Exception:
        extra_html = '<p>Графики/таблицы эффективности недоступны</p>'

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
                {extra_html}
            </body>
        </html>
        """
    file_path.write_text(html_content, encoding="utf-8")


def _has_extended_columns(df: Optional[pd.DataFrame], columns: tuple[str, ...]) -> bool:
    """Проверяет наличие расширенных колонок в DataFrame."""
    return df is not None and any(col in df.columns for col in columns)


def _build_efficiency_frame(plans: Optional[pd.DataFrame], facts: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Строит агрегированную таблицу эффективности по цехам из плановых и фактических данных."""
    if plans is None or facts is None:
        return None
    if not _has_extended_columns(plans, ("plan_energy", "plan_time")):
        return None
    if not _has_extended_columns(facts, ("fact_energy", "fact_time")):
        return None

    plan_agg = (
        plans.groupby("workshop", dropna=False)
        .agg(plan_qty=("plan_qty", "sum"), plan_energy=("plan_energy", "sum"), plan_time=("plan_time", "sum"))
        .reset_index()
    )
    fact_agg = (
        facts.groupby("workshop", dropna=False)
        .agg(fact_qty=("fact_qty", "sum"), fact_energy=("fact_energy", "sum"), fact_time=("fact_time", "sum"))
        .reset_index()
    )

    eff = pd.merge(plan_agg, fact_agg, on="workshop", how="outer").fillna(0)
    eff["energy_deviation"] = eff["fact_energy"] - eff["plan_energy"]
    eff["time_deviation"] = eff["fact_time"] - eff["plan_time"]
    eff["energy_intensity_plan"] = (eff["plan_energy"] / eff["plan_qty"]).replace([float("inf"), float("nan")], 0.0)
    eff["energy_intensity_fact"] = (eff["fact_energy"] / eff["fact_qty"]).replace([float("inf"), float("nan")], 0.0)
    eff["time_intensity_plan"] = (eff["plan_time"] / eff["plan_qty"]).replace([float("inf"), float("nan")], 0.0)
    eff["time_intensity_fact"] = (eff["fact_time"] / eff["fact_qty"]).replace([float("inf"), float("nan")], 0.0)
    eff["time_utilization"] = (eff["plan_time"] / eff["fact_time"] * 100.0).replace([float("inf"), float("nan")], 0.0)
    return eff
