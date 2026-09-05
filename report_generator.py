"""
report_generator.py

Generates a downloadable PDF summary of a scan result - so an officer
can print/attach it to a case file.

Visual language matches the Streamlit app: a navy header banner, a
colour-coded risk badge (green/amber/red), and horizontal meter bars
for the score breakdown - so the printed report reads as the same
product as the on-screen dashboard, not a plain text dump.
"""

from fpdf import FPDF
from datetime import datetime

from fraud_score import WEIGHTS

# ---- palette (mirrors the app's CSS custom properties) ----
NAVY_DARK = (10, 17, 32)
NAVY_ACCENT_LINE = (36, 198, 200)
TEAL = (28, 150, 152)
SAFFRON = (224, 122, 24)
GREEN = (30, 150, 90)
RED = (200, 55, 62)
TEXT_DARK = (26, 34, 50)
MUTED = (110, 124, 145)
TRACK_BG = (231, 235, 241)
ROW_ALT = (241, 245, 250)

RISK_COLOR = {"low": GREEN, "medium": SAFFRON, "high": RED}

LABEL_TO_WEIGHT_KEY = {
    "Tampering / Forgery": "tampering",
    "Metadata": "metadata",
    "Font Consistency": "font",
    "AI-Generated Document Check": "ai_generated",
    "Document Validation": "validation",
    "Face Verification": "face_match",
}


def safe(text):
    """Core Helvetica font is latin-1 only - strip anything it can't render."""
    return str(text).encode("latin-1", "ignore").decode("latin-1")


class ScreeningReportPDF(FPDF):
    generated_str = ""

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(*TRACK_BG)
        self.set_line_width(0.2)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(
            0, 10,
            f"Page {self.page_no()}  |  CONFIDENTIAL - For Official Use Only  |  Generated {self.generated_str}",
            align="C"
        )


def _section_title(pdf, text, accent=NAVY_ACCENT_LINE):
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12.5)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(0, 7, safe(text), ln=1)
    y = pdf.get_y()
    pdf.set_draw_color(*accent)
    pdf.set_line_width(0.9)
    pdf.line(15, y, 42, y)
    pdf.set_line_width(0.2)
    pdf.ln(3.5)


def _kv_table(pdf, rows, empty_message="No data available."):
    if not rows:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 7, safe(empty_message), ln=1)
        return
    pdf.set_font("Helvetica", "", 10)
    row_h = 7
    for i, (key, value) in enumerate(rows):
        fill = ROW_ALT if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*fill)
        pdf.set_text_color(*MUTED)
        pdf.cell(68, row_h, safe(key), fill=True, border=0)
        pdf.set_text_color(*TEXT_DARK)
        pdf.cell(0, row_h, safe(value), fill=True, ln=1, border=0)


def _issues_list(pdf, issues, ok_message):
    if not issues:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GREEN)
        pdf.cell(0, 7, safe(ok_message), ln=1)
        return
    for issue in issues:
        y = pdf.get_y()
        pdf.set_fill_color(*RED)
        pdf.rect(15, y + 1.6, 2.2, 2.2, "F")
        pdf.set_xy(20, y)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(pdf.w - 35, 5.5, safe(issue))
        pdf.ln(1)


def _bar_row(pdf, label, pts, max_pts):
    max_pts = max(max_pts, 1)
    pct = min(1.0, pts / max_pts)
    color = GREEN if pts == 0 else (RED if pts >= max_pts else SAFFRON)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(120, 6, safe(label))
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, f"{pts} / {max_pts} pts", align="R", ln=1)

    bar_x, bar_h = 15, 3
    bar_y = pdf.get_y() + 1
    bar_w = pdf.w - 30
    pdf.set_fill_color(*TRACK_BG)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")
    fill_w = bar_w * pct
    if fill_w > 0:
        pdf.set_fill_color(*color)
        pdf.rect(bar_x, bar_y, fill_w, bar_h, "F")
    pdf.set_y(bar_y + bar_h + 5)


def generate_pdf_report(doc_type, fields, validation_result, fraud_result,
                         ocr_result, ai_gen_result, face_result, save_path="scan_report.pdf"):
    pdf = ScreeningReportPDF(format="A4")
    pdf.generated_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    # ---------------- Header banner ----------------
    pdf.set_fill_color(*NAVY_DARK)
    pdf.rect(0, 0, pdf.w, 30, "F")
    pdf.set_fill_color(*NAVY_ACCENT_LINE)
    pdf.rect(0, 30, pdf.w, 1.2, "F")

    pdf.set_xy(15, 8)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "Document Screening Report", ln=1)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(180, 198, 212)
    pdf.cell(0, 6, "AI-Based Fake Identity & Document Screening System  |  MHA / SSB  |  PS 26188", ln=1)

    pdf.set_xy(15, 38)

    # ---------------- Meta row ----------------
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MUTED)
    pdf.cell(32, 6, "Document Type:", ln=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(0, 6, safe(doc_type), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, f"Generated: {pdf.generated_str}", ln=1)
    pdf.ln(3)

    # ---------------- Risk verdict badge ----------------
    level = fraud_result["verdict_level"]
    risk_color = RISK_COLOR.get(level, MUTED)
    banner_y = pdf.get_y()
    banner_h = 22
    pdf.set_fill_color(*risk_color)
    pdf.rect(15, banner_y, pdf.w - 30, banner_h, "F")

    pdf.set_xy(20, banner_y + 3)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5, "RISK SCORE", ln=1)
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(38, 12, f"{fraud_result['final_score']}", ln=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(pdf.get_x(), banner_y + 9)
    pdf.cell(15, 6, "/100", ln=0)

    pdf.set_xy(72, banner_y + 6)
    pdf.set_font("Helvetica", "B", 12.5)
    pdf.multi_cell(pdf.w - 92, 6, safe(fraud_result["verdict"]))

    pdf.set_y(banner_y + banner_h + 8)

    # ---------------- Score breakdown ----------------
    _section_title(pdf, "Score Breakdown")
    for label, pts in fraud_result["breakdown"].items():
        max_pts = WEIGHTS.get(LABEL_TO_WEIGHT_KEY.get(label, ""), max(pts, 1))
        _bar_row(pdf, label, pts, max_pts)

    # ---------------- Extracted fields ----------------
    _section_title(pdf, "Extracted Fields (OCR)")
    _kv_table(pdf, list(fields.items()) if fields else [],
              empty_message="No fields could be confidently extracted.")

    # ---------------- Document validation ----------------
    _section_title(pdf, "Document Validation")
    _issues_list(pdf, validation_result["issues"],
                 ok_message="No validation issues found - document fields look consistent.")

    # ---------------- Tampering / AI-generation summary ----------------
    _section_title(pdf, "Tampering & AI-Generation Signals")
    font_check = ocr_result.get("font_check", {})
    if ai_gen_result.get("available"):
        ai_summary = (
            f"{'Likely AI-generated' if ai_gen_result.get('is_ai_generated') else 'Likely a real captured document'} "
            f"(confidence: {ai_gen_result.get('confidence', 0)}%)"
        )
    else:
        ai_summary = "Unavailable (transformers/torch not installed on this machine)."
    _kv_table(pdf, [
        ("AI-Generation Check", ai_summary),
        ("Font Consistency", font_check.get("reason", "Not evaluated.")),
    ])

    # ---------------- Face verification ----------------
    _section_title(pdf, "Face Verification")
    fm = face_result["face_match"]
    live = face_result["liveness"]
    if fm.get("error"):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*RED)
        pdf.cell(0, 7, safe("Face verification could not be completed."), ln=1)
    else:
        _kv_table(pdf, [
            ("Faces Matched", str(fm["verified"])),
            ("Distance Score (lower = more similar)", str(fm["distance"])),
            ("Live Capture Sharpness", str(live["sharpness_score"])),
            ("Possible Spoof", str(live["possible_spoof"])),
        ])

    pdf.output(save_path)
    return save_path
