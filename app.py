"""
app.py

AI-Based Fake Identity & Document Screening System
Smart India Hackathon | PS ID: 26188 | Ministry of Home Affairs (SSB)
Theme: Blockchain & Cybersecurity

Main Streamlit app tying together all 4 modules from the problem
statement:
  1. OCR Extraction        -> ocr_extraction.py
  2. Document Validation   -> document_validation.py
  3. Tampering Detection   -> ela_check.py, copy_move_check.py, metadata_check.py, ai_generated_check.py
  4. Face Verification     -> face_verification.py

Run with:  streamlit run app.py
"""

import os
import streamlit as st

from preprocessing import preprocess_pipeline
from ela_check import run_ela
from copy_move_check import detect_copy_move
from metadata_check import check_metadata
from ocr_extraction import run_ocr_extraction, LANGUAGE_OPTIONS
from document_validation import validate_document
from ai_generated_check import run_ai_generated_check
from face_verification import run_face_verification
from fraud_score import calculate_fraud_score, WEIGHTS
from report_generator import generate_pdf_report
from db import log_scan, get_recent_scans

st.set_page_config(
    page_title="Document Screening System | MHA",
    page_icon="🛂",
    layout="wide"
)

# ---------------------------------------------------------------
# Theme: a "forensics console" look — dark slate/navy surface (the
# screening desk), a cyan scan-line accent (the tech/AI layer), and a
# thin saffron-to-green rule under the header referencing the
# emblem colours without leaning on the literal tricolour block.
# ---------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

:root {
    --bg-base: #0a1120;
    --bg-panel: #121c30;
    --bg-panel-alt: #17233a;
    --accent-teal: #24c6c8;
    --accent-saffron: #ff9a3c;
    --accent-green: #34c777;
    --risk-high: #f0525a;
    --risk-med: #ff9a3c;
    --risk-low: #34c777;
    --text-primary: #e9eef7;
    --text-muted: #8fa0ba;
    --border-subtle: rgba(255,255,255,0.08);
}

html, body, [class*="css"], .stMarkdown, p, span, label, div {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 12% -10%, #16253f 0%, var(--bg-base) 42%) fixed;
    color: var(--text-primary);
}

section[data-testid="stSidebar"] {
    background-color: #0d1526;
    border-right: 1px solid var(--border-subtle);
}
section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--border-subtle); }

/* ---------------- Header ---------------- */
.gov-header {
    background: linear-gradient(120deg, #0c1a30 0%, #123252 55%, #0f3d47 100%);
    padding: 30px 34px 26px 34px;
    border-radius: 10px;
    border: 1px solid var(--border-subtle);
    position: relative;
    overflow: hidden;
    margin-bottom: 0;
}
.gov-header::after {
    content: "";
    position: absolute; top: -40%; right: -5%; bottom: -40%; width: 260px;
    background: radial-gradient(circle, rgba(36,198,200,0.22), transparent 70%);
}
.gov-header .eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.03em;
    color: var(--accent-teal);
    margin: 0 0 10px 0;
    position: relative; z-index: 1;
}
.gov-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    margin: 0;
    font-size: 27px;
    font-weight: 700;
    color: #f4f7fb;
    position: relative; z-index: 1;
}
.gov-header p {
    margin: 8px 0 0 0;
    font-size: 14px;
    color: var(--text-muted);
    position: relative; z-index: 1;
}
.tricolor-strip {
    height: 3px;
    background: linear-gradient(90deg, var(--accent-saffron) 0%, #eef3fa 50%, var(--accent-green) 100%);
    border-radius: 2px;
    margin: 12px 0 26px 0;
    opacity: 0.9;
}

/* ---------------- Panels ---------------- */
.section-card {
    background: var(--bg-panel);
    padding: 20px 24px;
    border-radius: 8px;
    border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent-teal);
    margin-bottom: 18px;
}
.section-card h3 { margin-top: 0; }

h1, h2, h3, h4, h5 { color: var(--text-primary); font-family: 'Space Grotesk', sans-serif; }
.stMarkdown p, .stMarkdown li, .stCaption, small { color: var(--text-muted); }
.stMarkdown strong { color: var(--text-primary); }

/* ---------------- Score ring + verdict ---------------- */
.score-ring {
    width: 148px; height: 148px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 4px auto 0 auto;
}
.score-ring-inner {
    width: 116px; height: 116px; border-radius: 50%;
    background: var(--bg-panel);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.score-value { font-family: 'JetBrains Mono', monospace; font-size: 34px; font-weight: 700; line-height: 1; color: var(--text-primary); }
.score-outof { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.verdict-pill {
    display: inline-block; padding: 8px 18px; border-radius: 20px;
    font-weight: 600; font-size: 14px; font-family: 'Inter', sans-serif;
    margin-bottom: 14px;
}
.verdict-low { background: rgba(52,199,119,0.14); color: var(--risk-low); border: 1px solid rgba(52,199,119,0.4); }
.verdict-medium { background: rgba(255,154,60,0.14); color: var(--risk-med); border: 1px solid rgba(255,154,60,0.4); }
.verdict-high { background: rgba(240,82,90,0.14); color: var(--risk-high); border: 1px solid rgba(240,82,90,0.4); }

.bar-row { margin-bottom: 12px; }
.bar-label { display: flex; justify-content: space-between; font-size: 13px; color: var(--text-muted); margin-bottom: 5px; }
.bar-label b { color: var(--text-primary); font-weight: 500; }
.bar-track { background: rgba(255,255,255,0.07); border-radius: 6px; height: 8px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 6px; }

/* ---------------- History cards (sidebar) ---------------- */
.history-item {
    background: var(--bg-panel-alt);
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 10px;
    border-left: 3px solid var(--text-muted);
    font-size: 12.5px;
}
.history-item .h-doc { color: var(--text-primary); font-weight: 600; }
.history-item .h-meta { color: var(--text-muted); font-family: 'JetBrains Mono', monospace; font-size: 11.5px; }

/* ---------------- Widget restyling ---------------- */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(120deg, var(--accent-teal), #1a8fa0);
    color: #06131a; font-weight: 700; border: none; border-radius: 6px;
    padding: 0.6em 1.2em; transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px); box-shadow: 0 6px 18px rgba(36,198,200,0.25); color: #06131a;
}

div[data-testid="stFileUploaderDropzone"], section[data-testid="stFileUploadDropzone"] {
    background: var(--bg-panel-alt) !important;
    border: 1.5px dashed rgba(36,198,200,0.4) !important;
    border-radius: 8px !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    background-color: var(--bg-panel-alt);
    border-color: var(--border-subtle);
    color: var(--text-primary);
}

div[data-testid="stExpander"] {
    background: var(--bg-panel);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    margin-bottom: 10px;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent-teal), var(--accent-green));
}

hr { border-color: var(--border-subtle) !important; }

[data-testid="stAlert"] { border-radius: 8px; }

table { color: var(--text-primary) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="gov-header">
    <p class="eyebrow">MHA · SASHASTRA SEEMA BAL (SSB) · PROBLEM STATEMENT 26188</p>
    <h1>🛂 AI-Based Fake Identity &amp; Document Screening System</h1>
    <p>Border-checkpoint document forensics — OCR, tamper detection, generative-AI
    detection and face verification in one screening pass.</p>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="tricolor-strip"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------
# Sidebar: recent scan history (digital trail for investigations)
# ---------------------------------------------------------------
LEVEL_COLOR = {"LOW": "var(--risk-low)", "MEDIUM": "var(--risk-med)", "HIGH": "var(--risk-high)"}

with st.sidebar:
    st.subheader("📋 Recent Scan History")
    recent = get_recent_scans(limit=8)
    if recent:
        for ts, doc_type, score, verdict in recent:
            level_word = verdict.split(" ")[0]  # LOW / MEDIUM / HIGH
            color = LEVEL_COLOR.get(level_word, "var(--text-muted)")
            st.markdown(f"""
            <div class="history-item" style="border-left-color:{color};">
                <div class="h-doc">{doc_type}</div>
                <div class="h-meta">{ts}</div>
                <div style="margin-top:4px;">Score: <b>{score}/100</b> — {verdict.split(' - ')[0]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No scans yet. Run your first scan to see history here.")

# ---------------------------------------------------------------
# Main input section
# ---------------------------------------------------------------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Step 1 — Document Details & Upload")

col_a, col_b = st.columns(2)
with col_a:
    doc_type = st.selectbox(
        "Document Type",
        ["Passport", "Visa", "National ID", "Driving License", "Permit"]
    )
with col_b:
    lang_label = st.selectbox("OCR Language", list(LANGUAGE_OPTIONS.keys()))
    lang_code = LANGUAGE_OPTIONS[lang_label]

col1, col2 = st.columns(2)
with col1:
    doc_file = st.file_uploader("Upload Document Image", type=["jpg", "jpeg", "png"])
with col2:
    selfie_file = st.file_uploader("Upload Live Capture (Selfie)", type=["jpg", "jpeg", "png"])
st.markdown('</div>', unsafe_allow_html=True)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_file(uploaded_file, filename):
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


# Maps each score-breakdown label back to its max possible weight, so
# the meter bars can show "12 / 25 pts" rather than a bare number.
LABEL_TO_WEIGHT_KEY = {
    "Tampering / Forgery": "tampering",
    "Metadata": "metadata",
    "Font Consistency": "font",
    "AI-Generated Document Check": "ai_generated",
    "Document Validation": "validation",
    "Face Verification": "face_match",
}


def render_score_ring(score, level):
    color = {"low": "var(--risk-low)", "medium": "var(--risk-med)", "high": "var(--risk-high)"}[level]
    st.markdown(f"""
    <div class="score-ring" style="background: conic-gradient({color} {score}%, rgba(255,255,255,0.08) 0);">
        <div class="score-ring-inner">
            <div class="score-value">{score}</div>
            <div class="score-outof">/ 100</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_breakdown_bars(breakdown):
    rows = []
    for label, pts in breakdown.items():
        max_pts = WEIGHTS.get(LABEL_TO_WEIGHT_KEY.get(label, ""), max(pts, 1))
        pct = int(round((pts / max_pts) * 100)) if max_pts else 0
        if pts == 0:
            color = "var(--risk-low)"
        elif pct >= 100:
            color = "var(--risk-high)"
        else:
            color = "var(--accent-saffron)"
        rows.append(f"""
        <div class="bar-row">
            <div class="bar-label"><span>{label}</span><b>{pts} / {max_pts} pts</b></div>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%; background:{color};"></div></div>
        </div>
        """)
    st.markdown("".join(rows), unsafe_allow_html=True)


if doc_file is not None and selfie_file is not None:
    doc_path = save_uploaded_file(doc_file, "document.jpg")
    selfie_path = save_uploaded_file(selfie_file, "selfie.jpg")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    prev1, prev2 = st.columns(2)
    with prev1:
        st.image(doc_path, caption="Uploaded Document", width=320)
    with prev2:
        st.image(selfie_path, caption="Live Capture", width=320)

    run_scan = st.button("🔍 Run Full Screening", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if run_scan:
        with st.spinner("Running preprocessing..."):
            preprocessed_path = preprocess_pipeline(doc_path)

        with st.spinner("Module 1: Extracting text (OCR)..."):
            ocr_result = run_ocr_extraction(preprocessed_path, doc_type=doc_type, lang_code=lang_code)

        with st.spinner("Module 2: Validating document fields..."):
            validation_result = validate_document(ocr_result["fields"], doc_type)

        with st.spinner("Module 3: Checking for tampering (ELA, copy-move, metadata, AI-generation)..."):
            ela_result = run_ela(doc_path)
            copy_move_result = detect_copy_move(doc_path)
            metadata_result = check_metadata(doc_path)
            ai_gen_result = run_ai_generated_check(doc_path)

        with st.spinner("Module 4: Verifying face match..."):
            face_result = run_face_verification(doc_path, selfie_path)

        fraud_result = calculate_fraud_score(
            ela_result, copy_move_result, metadata_result,
            ocr_result, validation_result, ai_gen_result, face_result
        )

        log_scan(doc_type, fraud_result["final_score"], fraud_result["verdict"])

        # ---------------- Final verdict ----------------
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Final Result")

        level = fraud_result["verdict_level"]
        result_col1, result_col2 = st.columns([1, 2])
        with result_col1:
            render_score_ring(fraud_result["final_score"], level)
        with result_col2:
            st.markdown(
                f'<div class="verdict-pill verdict-{level}">{fraud_result["verdict"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown("**Score Breakdown**")
            render_breakdown_bars(fraud_result["breakdown"])
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------- PDF report download ----------------
        pdf_path = generate_pdf_report(
            doc_type, ocr_result["fields"], validation_result,
            fraud_result, ocr_result, ai_gen_result, face_result
        )
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download Full PDF Report", f, file_name="scan_report.pdf")

        # ---------------- Detailed breakdown ----------------
        st.markdown("---")
        st.subheader("Detailed Module Results")

        with st.expander("📝 Module 1 — OCR Extraction"):
            st.write("**Extracted Fields:**")
            if ocr_result["fields"]:
                st.table(ocr_result["fields"])
            else:
                st.info("No structured fields could be confidently extracted.")
            st.text_area("Raw OCR Text", ocr_result["raw_text"], height=120)

        with st.expander("✅ Module 2 — Document Validation"):
            if validation_result["issues"]:
                for issue in validation_result["issues"]:
                    st.error(issue)
            else:
                st.success("No validation issues found - document fields look consistent.")

        with st.expander("🔍 Module 3 — Tampering Detection"):
            st.write(f"**Error Level Analysis:** {ela_result['flagged_block_count']} suspicious region(s) found "
                      f"(flagged: {ela_result['flag']})")
            st.image(ela_result["ela_overlay_path"],
                     caption="Suspicious regions highlighted in red (if any) - normal text is NOT flagged")
            st.write(f"**Copy-Move / Stamp Duplication:** {copy_move_result['reason']}")
            st.write(f"**Metadata:** {metadata_result['reason']}")
            if ai_gen_result["available"]:
                verdict_txt = "Likely AI-generated" if ai_gen_result["is_ai_generated"] else "Likely a real captured document"
                st.write(f"**AI-Generation Check (deep learning model):** {verdict_txt} "
                          f"(confidence: {ai_gen_result['confidence']}%)")
            else:
                st.warning(ai_gen_result["error"])

        with st.expander("🙂 Module 4 — Face Verification"):
            fm = face_result["face_match"]
            live = face_result["liveness"]
            if fm["error"]:
                st.error(f"Face verification error: {fm['error']}")
            else:
                st.write(f"**Faces Matched:** {fm['verified']}")
                st.write(f"**Distance Score** (lower = more similar): {fm['distance']}")
            st.write(f"**Live Capture Sharpness:** {live['sharpness_score']} "
                      f"(possible spoof: {live['possible_spoof']})")

else:
    st.info("Upload both a document image and a live capture above, then click **Run Full Screening**.")
