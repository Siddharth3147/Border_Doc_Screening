"""
ocr_extraction.py

Module 1 from the problem statement: OCR Extraction.

Improvements vs the first version of this project:
- Multi-language OCR support (earlier version only read English text,
  which is useless for Aadhaar/National ID cards that are printed in
  Hindi + regional languages alongside English).
- Extracts actual structured fields (Name, Document Number, DOB,
  Expiry Date etc.) depending on document type, instead of just
  dumping raw OCR text.

LANGUAGE SUPPORT NOTE:
Tesseract needs separate language data files for each language.
'eng' (English) comes by default. For Hindi, Tamil, Telugu, Bengali
etc. you need to install the matching tessdata files - see README.
Default here is "eng+hin" (English + Hindi) since that covers most
Indian national ID documents. You can pass a different lang_code for
other regional documents.
"""

import re
import pytesseract
import cv2

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

LANGUAGE_OPTIONS = {
    "English + Hindi (default)": "eng+hin",
    "English only": "eng",
    "English + Tamil": "eng+tam",
    "English + Telugu": "eng+tel",
    "English + Bengali": "eng+ben",
    "English + Marathi": "eng+mar",
}


def extract_text(image_path, lang_code="eng+hin"):
    img = cv2.imread(image_path)
    try:
        text = pytesseract.image_to_string(img, lang=lang_code)
    except pytesseract.TesseractError:
        # requested language pack not installed on this machine - fall back to English
        text = pytesseract.image_to_string(img, lang="eng")
    return text.strip()


def check_font_consistency(image_path, lang_code="eng+hin"):
    """
    Heuristic: measures variation in detected text height. Large,
    inconsistent variation MAY suggest mixed fonts/sizes (e.g. an
    edited name pasted in a different font) - not a certainty, just
    one signal among several.
    """
    img = cv2.imread(image_path)
    try:
        data = pytesseract.image_to_data(img, lang=lang_code, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractError:
        data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)

    heights = []
    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        conf_raw = data["conf"][i]
        conf = int(conf_raw) if str(conf_raw).lstrip("-").isdigit() else -1
        if word and conf > 40:
            heights.append(data["height"][i])

    if len(heights) < 3:
        return {"flagged": False, "reason": "Not enough text detected for font analysis."}

    import numpy as np
    avg_height = float(np.mean(heights))
    std_dev = float(np.std(heights))
    ratio = std_dev / avg_height if avg_height > 0 else 0
    flagged = ratio > 0.4  # slightly relaxed vs before, real documents do mix header/body sizes

    return {
        "flagged": flagged,
        "reason": "Inconsistent font sizes detected." if flagged else "Font sizes look consistent."
    }


# --- Field extraction patterns per document type ---
# These are simple regex based extractors. Real production systems
# use dedicated MRZ parsers for passports and layout-aware models for
# ID cards, but this is a solid starting point for a prototype.

def extract_fields(text, doc_type):
    fields = {}

    dob_match = re.search(r"(?:DOB|Date of Birth|जन्म)[:\s]*([0-3]?\d[/-][01]?\d[/-]\d{2,4})", text, re.IGNORECASE)
    if dob_match:
        fields["Date of Birth"] = dob_match.group(1)

    expiry_match = re.search(r"(?:Expiry|Valid Till|Date of Expiry)[:\s]*([0-3]?\d[/-][01]?\d[/-]\d{2,4})", text, re.IGNORECASE)
    if expiry_match:
        fields["Date of Expiry"] = expiry_match.group(1)

    gender_match = re.search(r"\b(Male|Female|MALE|FEMALE|M|F)\b", text)
    if gender_match:
        fields["Gender"] = gender_match.group(1)

    if doc_type == "Passport":
        passport_no = re.search(r"\b([A-PR-WYa-pr-wy][0-9]{7})\b", text)
        if passport_no:
            fields["Passport Number"] = passport_no.group(1)
        nationality = re.search(r"(?:Nationality)[:\s]*([A-Za-z]+)", text, re.IGNORECASE)
        if nationality:
            fields["Nationality"] = nationality.group(1)

    elif doc_type == "Visa":
        visa_no = re.search(r"(?:Visa No\.?|Visa Number)[:\s]*([A-Z0-9]{6,12})", text, re.IGNORECASE)
        if visa_no:
            fields["Visa Number"] = visa_no.group(1)
        visa_type = re.search(r"(?:Visa Type|Type)[:\s]*([A-Za-z\-]+)", text, re.IGNORECASE)
        if visa_type:
            fields["Visa Type"] = visa_type.group(1)
        stay = re.search(r"(?:Stay Duration|Duration)[:\s]*(\d+\s*(?:days|months|years))", text, re.IGNORECASE)
        if stay:
            fields["Stay Duration"] = stay.group(1)

    elif doc_type in ("National ID", "Driving License", "Permit"):
        id_no = re.search(r"\b(\d{4}\s?\d{4}\s?\d{4})\b", text)  # Aadhaar-style 12 digit
        if id_no:
            fields["Document Number"] = id_no.group(1)

    # Name is the hardest to reliably regex-extract from noisy OCR text
    # across formats, so we grab the first plausible-looking text line
    # as a best-effort guess and let the user verify/correct it.
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name_guess = None
    for line in lines:
        letters_only = re.sub(r"[^A-Za-z\s]", "", line)
        if len(letters_only) >= 4 and len(letters_only.split()) <= 5 and letters_only.isupper() is False:
            name_guess = line
            break
    if name_guess:
        fields["Name (best guess - please verify)"] = name_guess

    return fields


def run_ocr_extraction(image_path, doc_type="National ID", lang_code="eng+hin"):
    raw_text = extract_text(image_path, lang_code)
    fields = extract_fields(raw_text, doc_type)
    font_result = check_font_consistency(image_path, lang_code)
    return {
        "raw_text": raw_text,
        "fields": fields,
        "font_check": font_result
    }


if __name__ == "__main__":
    result = run_ocr_extraction("sample_images/sample_id.jpg", doc_type="National ID")
    print(result)
