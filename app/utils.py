from __future__ import annotations

import os
from datetime import datetime

from fpdf import FPDF


def has_api_keys() -> bool:
    """Return True if at least one LLM provider is usable."""
    return bool(
        os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
    )


def _truncate(text: str, limit: int = 115) -> str:
    """Truncate at a word boundary to avoid mid-word cuts."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def _pdf_str(text: str) -> str:
    """Sanitize a string for fpdf2 built-in fonts (Latin-1 only).

    Replaces common non-Latin-1 characters with ASCII equivalents and drops
    anything that still can't be encoded, preventing FPDFUnicodeEncodingException.
    """
    _REPLACEMENTS = {
        "\u2014": "--",   # em dash —
        "\u2013": "-",    # en dash –
        "\u2018": "'",    # left single quote '
        "\u2019": "'",    # right single quote '
        "\u201c": '"',    # left double quote "
        "\u201d": '"',    # right double quote "
        "\u2026": "...",  # ellipsis …
        "\u00a0": " ",    # non-breaking space
        "\u2022": "-",    # bullet •
        "\u2019": "'",    # apostrophe variant
    }
    for char, replacement in _REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="ignore").decode("latin-1")


def fmt_unit(unit: str) -> str:
    _MAP = {
        "$": "$ USD", "usd": "$ USD", "dollars": "$ USD",
        "£": "£ GBP", "gbp": "£ GBP",
        "€": "€ EUR", "eur": "€ EUR",
    }
    return _MAP.get(unit.lower(), unit.capitalize())


def export_filename(company_name: str, product_name: str) -> str:
    """Generate a clean export filename: {company}_{product}_{date}.pdf"""
    def sanitize(s: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in s).strip("_")

    date_str = datetime.now().strftime("%Y%m%d")
    company_safe = sanitize(company_name)[:20]
    product_safe = sanitize(product_name)[:20]
    return f"{company_safe}_{product_safe}_{date_str}.pdf"


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
    pdf.cell(0, 5, _pdf_str(scenario_name), new_x="LMARGIN", new_y="NEXT")

    # ── Meta line ────────────────────────────────────────────────────────────
    pdf.set_xy(20, 35)
    pdf.set_text_color(*GRAY)
    pdf.set_font("Helvetica", "", 8)
    timestamp = datetime.now().strftime("%b %d, %Y")
    meta = _pdf_str(
        f"{customer.company_name}  ·  {customer.industry}  ·  "
        f"{customer.company_size}  ·  Product: {product_name}  ·  {timestamp}"
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

    col_widths = [112, 30, 28]

    # Table header row
    pdf.set_fill_color(*LIGHT)
    pdf.set_text_color(*GRAY)
    pdf.set_font("Helvetica", "B", 8)
    for w, label in zip(col_widths, ["Field", "Unit", "Value"]):
        pdf.cell(w, 6, label, fill=True)
    pdf.ln()

    # Data rows
    for i, field in enumerate(calculator.fields):
        val = field.current_value if field.current_value is not None else field.ai_estimate

        if "$" in field.unit:
            val_str = f"{val:,.0f}"
        else:
            try:
                is_int = (
                    "%" not in field.unit
                    and float(field.ai_estimate) == int(field.ai_estimate)
                )
            except (ValueError, TypeError):
                is_int = False
            val_str = str(int(val)) if is_int else f"{val:,.2f}"

        fill_color = (252, 252, 254) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*fill_color)

        pdf.set_text_color(*DARK)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_widths[0], 6, _pdf_str(field.label)[:55], fill=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*GRAY)
        pdf.cell(col_widths[1], 6, _pdf_str(fmt_unit(field.unit))[:18], fill=True)
        pdf.set_text_color(*DARK)
        pdf.cell(col_widths[2], 6, val_str, fill=True)
        pdf.ln()

    pdf.ln(5)

    # ── ROI Summary ───────────────────────────────────────────────────────────
    section_header("ROI Summary")

    for metric in calculator.output_metrics:
        value_str = metric.format_value(calculator.fields)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*BLUE)
        pdf.cell(70, 7, _pdf_str(value_str))
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 7, _pdf_str(metric.label), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 4, _pdf_str(metric.description))
        pdf.ln(3)

    pdf.ln(4)

    # ── Rationale ────────────────────────────────────────────────────────────
    section_header("Methodology & Assumptions")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 60)
    pdf.multi_cell(0, 5, _pdf_str(calculator.rationale))

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_auto_page_break(False)
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, "Generated by Value Mapper  -  value-mapper.streamlit.app", align="C")

    return bytes(pdf.output())
