"""
document_validation.py

Module 2 from the problem statement: Document Validation.

Objective: verify whether the extracted information follows official
document standards / logical rules - and cross-check against a
database (here, a small local mock blacklist file standing in for a
real government database, since we don't have access to one for this
prototype).

Checks performed:
1. Is the document expired? (expiry date vs today)
2. Is the date of birth realistic? (not in the future, not >120 years ago)
3. Does the document number match a known blacklist entry?
4. Basic format sanity check on document/passport numbers.
"""

from datetime import datetime

# Mock blacklist - stands in for a real government database lookup.
# In production this would be an API call to an actual watchlist system.
MOCK_BLACKLIST_NUMBERS = {
    "A1234567",
    "999988887777",
    "Z9999999",
}


def _try_parse_date(date_str):
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def validate_document(fields, doc_type):
    issues = []
    today = datetime.now()

    # --- Expiry check ---
    expiry_str = fields.get("Date of Expiry")
    if expiry_str:
        expiry_date = _try_parse_date(expiry_str)
        if expiry_date:
            if expiry_date < today:
                issues.append(f"Document is EXPIRED (expiry date: {expiry_str}).")
        else:
            issues.append(f"Expiry date '{expiry_str}' could not be parsed - check format.")

    # --- DOB sanity check ---
    dob_str = fields.get("Date of Birth")
    if dob_str:
        dob_date = _try_parse_date(dob_str)
        if dob_date:
            age_years = (today - dob_date).days / 365.25
            if dob_date > today:
                issues.append("Date of birth is in the future - likely tampered.")
            elif age_years > 120:
                issues.append("Date of birth implies an unrealistic age (>120 years) - likely tampered.")
        else:
            issues.append(f"Date of birth '{dob_str}' could not be parsed - check format.")

    # --- Blacklist check ---
    doc_number = (
        fields.get("Passport Number")
        or fields.get("Visa Number")
        or fields.get("Document Number")
    )
    is_blacklisted = False
    if doc_number and doc_number.replace(" ", "") in MOCK_BLACKLIST_NUMBERS:
        is_blacklisted = True
        issues.append(f"Document number '{doc_number}' matches a BLACKLISTED entry.")

    # --- Missing critical fields ---
    if doc_type == "Passport" and "Passport Number" not in fields:
        issues.append("Could not extract a valid passport number - format may be non-standard or document unclear.")
    if doc_type == "Visa" and "Visa Number" not in fields:
        issues.append("Could not extract a valid visa number.")

    return {
        "issues": issues,
        "is_blacklisted": is_blacklisted,
        "flagged": len(issues) > 0,
    }


if __name__ == "__main__":
    sample_fields = {"Date of Expiry": "12/05/2020", "Date of Birth": "15/08/1990"}
    print(validate_document(sample_fields, "Passport"))
