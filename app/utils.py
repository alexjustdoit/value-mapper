from __future__ import annotations

import os

from fpdf import FPDF


def has_api_keys() -> bool:
    """Return True if at least one LLM provider is usable."""
    return bool(
        os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
    )


def fmt_unit(unit: str) -> str:
    _MAP = {
        "$": "$ USD", "usd": "$ USD", "dollars": "$ USD",
        "£": "£ GBP", "gbp": "£ GBP",
        "€": "€ EUR", "eur": "€ EUR",
    }
    return _MAP.get(unit.lower(), unit.capitalize())


def build_export_pdf(
    scenario_name: str,
    product_name: str,
    customer,
    calculator,
) -> bytes:
    """Return a styled PDF export of the calculator as bytes."""

    BLUE = (59, 130, 246)
    DARK = (30, 30, 40)
    GRAY = (100, 100, 110)
    LIGHT = (245, 245, 248)

    pdf = FPDF()
    pdf.set_margins(20, 15, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pw = pdf.w - pdf.l_margin - pdf.r_margin  # usable width in mm

    # ── Blue header ──────────────────────────────────────────────────────────
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, pdf.w, 30, style="F")
    pdf.set_xy(20, 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 7, "ROI Calculator", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, scenario_name, new_x="LMARGIN", new_y="NEXT")

    # ── Meta line ────────────────────────────────────────────────────────────
    pdf.set_xy(20, 35)
    pdf.set_text_color(*GRAY)
    pdf.set_font("Helvetica", "", 8)
    meta = (
        f"{customer.company_name}  ·  {customer.industry}  ·  "
        f"{customer.company_size}  ·  Product: {product_name}"
    )
    pdf.cell(0, 5, meta, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Section header helper ─────────────────────────────────────────────────
    def section_header(title: str) -> None:
        pdf.set_text_color(*DARK)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*BLUE)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pw, pdf.get_y())
        pdf.ln(3)

    # ── Inputs ────────────────────────────────────────────────────────────────
    section_header("Inputs")

    col_widths = [75, 28, 30, 37]

    # Table header row
    pdf.set_fill_color(*LIGHT)
    pdf.set_text_color(*GRAY)
    pdf.set_font("Helvetica", "B", 8)
    for w, label in zip(col_widths, ["Field", "Unit", "Value", "Source"]):
        pdf.cell(w, 5, label, fill=True)
    pdf.ln()

    # Data rows
    for i, field in enumerate(calculator.fields):
        val = field.current_value if field.current_value is not None else field.ai_estimate
        source = "Adjusted" if field.current_value is not None else "AI estimate"

        try:
            is_int = (
                "$" not in field.unit
                and "%" not in field.unit
                and float(field.ai_estimate) == int(field.ai_estimate)
            )
        except (ValueError, TypeError):
            is_int = False
        val_str = str(int(val)) if is_int else f"{val:,.2f}"

        fill_color = (252, 252, 254) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*fill_color)

        pdf.set_text_color(*DARK)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_widths[0], 5, field.label[:42], fill=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*GRAY)
        pdf.cell(col_widths[1], 5, fmt_unit(field.unit)[:18], fill=True)
        pdf.set_text_color(*DARK)
        pdf.cell(col_widths[2], 5, val_str, fill=True)
        if source == "Adjusted":
            pdf.set_text_color(210, 95, 30)
        else:
            pdf.set_text_color(55, 135, 75)
        pdf.cell(col_widths[3], 5, source, fill=True)
        pdf.ln()

        # Description sub-row
        pdf.set_text_color(*GRAY)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 4, field.description[:90])
        pdf.ln(5)

    pdf.ln(5)

    # ── ROI Summary ───────────────────────────────────────────────────────────
    section_header("ROI Summary")

    for metric in calculator.output_metrics:
        value_str = metric.format_value(calculator.fields)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*BLUE)
        pdf.cell(70, 7, value_str)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 7, metric.label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 4, metric.description)
        pdf.ln(3)

    pdf.ln(4)

    # ── Rationale ────────────────────────────────────────────────────────────
    section_header("Why These Metrics?")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 60)
    pdf.multi_cell(0, 5, calculator.rationale)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, "Generated by Value Mapper  ·  value-mapper.streamlit.app", align="C")

    return bytes(pdf.output())
