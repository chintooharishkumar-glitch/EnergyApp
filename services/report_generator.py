from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Mapping

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.energy_metrics import SummaryMetrics


def _build_table(df: pd.DataFrame, columns: list[str], title: str):
    if df.empty:
        return [Paragraph(f"<b>{title}</b> – No data", getSampleStyleSheet()["BodyText"]), Spacer(1, 8)]

    styles = getSampleStyleSheet()
    elems = [Paragraph(f"<b>{title}</b>", styles["Heading3"]), Spacer(1, 4)]

    data = [columns]
    for _, row in df[columns].iterrows():
        data.append([str(row[col]) for col in columns])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ]
        )
    )
    elems.append(table)
    elems.append(Spacer(1, 12))
    return elems


def build_pdf_report(
    title: str,
    summary: SummaryMetrics,
    room_metrics: pd.DataFrame,
    device_metrics: pd.DataFrame,
    controls: Mapping[str, object],
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "Smart Classroom Energy Monitoring report summarising usage, wasted energy, and potential cost savings.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 12))

    start = summary.start.strftime("%Y-%m-%d")
    end = summary.end.strftime("%Y-%m-%d")
    tariff = controls.get("tariff", 0.0)
    generated_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    meta_lines = [
        f"<b>Analysis period:</b> {start} to {end}",
        f"<b>Rooms analysed:</b> {summary.num_rooms}",
        f"<b>Tariff:</b> {tariff:.2f} per kWh",
        f"<b>Generated on:</b> {generated_on}",
    ]
    story.append(Paragraph("<br/>".join(meta_lines), styles["BodyText"]))
    story.append(Spacer(1, 16))

    kpi_lines = [
        f"<b>Total energy:</b> {summary.total_energy_kwh:.2f} kWh "
        f"(cost ${summary.total_cost:.2f})",
        f"<b>Total wasted energy:</b> {summary.total_wasted_kwh:.2f} kWh "
        f"(wasted cost ${summary.total_wasted_cost:.2f})",
        f"<b>Total wasted hours:</b> {summary.total_wasted_hours:.2f} h",
        f"<b>Share of energy wasted:</b> {summary.wasted_energy_pct:.1f}%",
    ]
    story.append(Paragraph("<br/>".join(kpi_lines), styles["BodyText"]))
    story.append(Spacer(1, 18))

    top_rooms = room_metrics.sort_values("wasted_cost", ascending=False).head(5)
    story.extend(
        _build_table(
            top_rooms,
            ["room_id", "energy_kwh", "wasted_energy_kwh", "wasted_hours", "wasted_cost", "wasted_pct"],
            "Top rooms by wasted cost",
        )
    )

    top_devices = device_metrics.sort_values("wasted_cost", ascending=False).head(5)
    story.extend(
        _build_table(
            top_devices,
            ["room_id", "device_type", "energy_kwh", "wasted_energy_kwh", "wasted_hours", "wasted_cost", "wasted_pct"],
            "Top devices by wasted cost",
        )
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

