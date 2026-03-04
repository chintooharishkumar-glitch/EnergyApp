"""
Generate a PDF document describing the Smart Classroom Energy Monitoring prototype.
Run: python scripts/generate_prototype_pdf.py
Output: Smart_Classroom_Energy_Prototype.pdf (in project root)
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_prototype_pdf(output_path: Path) -> None:
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(
        "Smart Classroom Energy Monitoring System",
        ParagraphStyle(name="Title", parent=styles["Title"], fontSize=22, spaceAfter=6),
    ))
    story.append(Paragraph("Prototype Overview & Documentation", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Overview
    story.append(Paragraph("<b>1. Overview</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This prototype is a web-based Smart Classroom Energy Monitoring system that detects "
        "when lights and AC are ON while the room is empty. The system calculates wasted energy "
        "hours and provides reports to reduce electricity costs.",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.2 * inch))

    # Features checklist
    story.append(Paragraph("<b>2. Delivered Features</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    feature_data = [
        ["Feature", "Description"],
        ["Upload data", "Upload classroom sensor data as CSV/Excel or load built-in sample data."],
        ["Dashboard charts", "Interactive charts: energy by room, time-series, activity heatmap."],
        ["Wasted energy calculation", "Automatic computation of wasted kWh, hours, and cost when equipment is ON in empty rooms."],
        ["PDF report download", "Generate and download a professional summary report with KPIs and rankings."],
        ["Professional UI", "Clean Streamlit UI with KPI cards, filters, and empty-state guidance."],
    ]
    t = Table(feature_data, colWidths=[1.4 * inch, 4.6 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5f4f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.25 * inch))

    # Architecture
    story.append(Paragraph("<b>3. Architecture</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Single Streamlit app (Python) serving as both frontend and backend. "
        "Core modules: app.py (navigation and pages), services/data_loader.py (CSV/Excel load and validation), "
        "services/energy_metrics.py (usage and wasted energy calculations), ui/charts.py (Plotly charts), "
        "services/report_generator.py (PDF reports), ui/layout.py (header, KPI cards, empty states).",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.2 * inch))

    # Tech stack
    story.append(Paragraph("<b>4. Technology Stack</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    tech_data = [["Component", "Technology"], ["App framework", "Streamlit"], ["Data", "Pandas"], ["Charts", "Plotly"], ["PDF generation", "ReportLab"]]
    t2 = Table(tech_data, colWidths=[2 * inch, 4 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.25 * inch))

    # Getting started
    story.append(Paragraph("<b>5. Getting Started</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("1. Install dependencies: pip install -r requirements.txt", styles["Normal"]))
    story.append(Paragraph("2. Run the app: streamlit run app.py", styles["Normal"]))
    story.append(Paragraph("3. Open http://localhost:8501 in your browser.", styles["Normal"]))
    story.append(Paragraph("4. Use 'Upload data' to upload a CSV/Excel file or click 'Load sample data'.", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    # Data format
    story.append(Paragraph("<b>6. Expected Data Format</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "CSV/Excel columns: timestamp (datetime), room_id, device_type (e.g. LIGHT, AC), "
        "status (ON/OFF or 1/0), occupancy (1 = occupied, 0 = empty). Optional: power_watts.",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph(
        "<i>Generated for the Smart Classroom Energy Monitoring prototype. "
        "Use the in-app Reports page to generate data-driven PDF reports from your uploaded dataset.</i>",
        ParagraphStyle(name="Italic", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))

    doc.build(story)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    out = root / "Smart_Classroom_Energy_Prototype.pdf"
    build_prototype_pdf(out)
    print(f"Generated: {out}")
