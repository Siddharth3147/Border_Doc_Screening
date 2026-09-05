"""
fraud_score.py

Combines every check into one final Risk Score (0-100, whole number)
and a verdict.

CHANGES vs the first version of this project (based on real feedback):
1. Score is now a plain whole number - no messy decimals.
2. Each check contributes its FULL weight only if it's actually
   flagged (mostly binary), instead of smoothly scaling a continuous
   value into the score. This naturally pushes results toward clearer
   LOW / HIGH outcomes and shrinks the vague "medium" middle zone,
   since a document either shows a real red flag or it doesn't -
   there's less room for everything to land in a mushy middle score.
3. Verdict bands were narrowed for the same reason: a manual-review
   verdict should be the exception, not the default outcome.
"""

WEIGHTS = {
    "tampering": 25,     # ELA + copy-move/stamp forgery
    "metadata": 10,
    "font": 10,
    "ai_generated": 20,  # real deep-learning generative-AI detector
    "validation": 15,    # expiry / DOB sanity / blacklist / format rules
    "face_match": 20,
}


def calculate_fraud_score(ela_result, copy_move_result, metadata_result,
                           ocr_result, validation_result, ai_gen_result,
                           face_result):
    score = 0
    breakdown = {}

    # --- Tampering (ELA outlier blocks OR copy-move stamp duplication) ---
    tampering_flagged = ela_result.get("flag", False) or copy_move_result.get("flag", False)
    tampering_pts = WEIGHTS["tampering"] if tampering_flagged else 0
    score += tampering_pts
    breakdown["Tampering / Forgery"] = tampering_pts

    # --- Metadata ---
    metadata_pts = WEIGHTS["metadata"] if metadata_result.get("flagged") else 0
    score += metadata_pts
    breakdown["Metadata"] = metadata_pts

    # --- Font consistency ---
    font_flagged = ocr_result.get("font_check", {}).get("flagged", False)
    font_pts = WEIGHTS["font"] if font_flagged else 0
    score += font_pts
    breakdown["Font Consistency"] = font_pts

    # --- AI-generated document detection ---
    ai_pts = 0
    if ai_gen_result.get("available") and ai_gen_result.get("is_ai_generated"):
        # scale slightly by model confidence, but still capped at the full weight
        confidence_fraction = min(1.0, ai_gen_result.get("confidence", 0) / 100)
        ai_pts = round(WEIGHTS["ai_generated"] * confidence_fraction)
    score += ai_pts
    breakdown["AI-Generated Document Check"] = ai_pts

    # --- Document validation (expiry, DOB, blacklist, format) ---
    validation_pts = WEIGHTS["validation"] if validation_result.get("flagged") else 0
    if validation_result.get("is_blacklisted"):
        validation_pts = WEIGHTS["validation"]  # blacklist hit always maxes this category
    score += validation_pts
    breakdown["Document Validation"] = validation_pts

    # --- Face match ---
    face_pts = 0
    fm = face_result.get("face_match", {})
    live = face_result.get("liveness", {})
    if fm.get("error") is None and not fm.get("verified", False):
        face_pts += round(WEIGHTS["face_match"] * 0.8)
    if live.get("possible_spoof", False):
        face_pts += round(WEIGHTS["face_match"] * 0.2)
    face_pts = min(face_pts, WEIGHTS["face_match"])
    score += face_pts
    breakdown["Face Verification"] = face_pts

    final_score = int(round(min(score, 100)))

    # narrower "needs review" band on purpose - see module docstring
    if final_score < 25:
        verdict = "LOW RISK - Document appears genuine"
        verdict_level = "low"
    elif final_score < 55:
        verdict = "MEDIUM RISK - Needs manual review"
        verdict_level = "medium"
    else:
        verdict = "HIGH RISK - Likely forged / fraudulent"
        verdict_level = "high"

    return {
        "final_score": final_score,
        "verdict": verdict,
        "verdict_level": verdict_level,
        "breakdown": breakdown
    }


if __name__ == "__main__":
    print(calculate_fraud_score(
        {"flag": False}, {"flag": False}, {"flagged": False},
        {"font_check": {"flagged": False}}, {"flagged": False, "is_blacklisted": False},
        {"available": True, "is_ai_generated": False, "confidence": 0},
        {"face_match": {"verified": True, "error": None}, "liveness": {"possible_spoof": False}}
    ))
