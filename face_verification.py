"""
face_verification.py

Module 4 from the problem statement: Face Verification.

Compares the photo on the ID/passport/visa document against a live
capture of the person, to confirm the document owner matches the
person presenting it.

Uses DeepFace (a genuine pretrained deep learning model - VGG-Face)
to generate face embeddings and compare them - this is real AI, not
a hand-written heuristic.

IMPORTANT: the basic "sharpness" liveness check is run ONLY on the
live selfie capture, never on the uploaded document photo. Government
ID documents are frequently low-resolution/faded by nature, so judging
them by sharpness would be meaningless and unfair - that check exists
purely to catch someone holding up a printed photo/screen to the
camera instead of their real face.
"""

from deepface import DeepFace
import cv2


def match_faces(id_photo_path, live_capture_path):
    try:
        result = DeepFace.verify(
            img1_path=id_photo_path,
            img2_path=live_capture_path,
            model_name="VGG-Face",
            enforce_detection=False
        )
        return {
            "verified": result["verified"],
            "distance": round(result["distance"], 3),
            "threshold": result["threshold"],
            "error": None
        }
    except Exception as e:
        return {"verified": False, "distance": None, "threshold": None, "error": str(e)}


def basic_liveness_check(live_capture_path):
    """
    Simple sharpness-based heuristic (variance of Laplacian) applied
    ONLY to the live capture - flags flat/blurry images that might be
    a photo-of-a-photo spoof attempt. Not a full anti-spoofing model.
    """
    img = cv2.imread(live_capture_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    possible_spoof = laplacian_var < 60
    return {
        "sharpness_score": round(float(laplacian_var), 1),
        "possible_spoof": bool(possible_spoof)
    }


def run_face_verification(id_photo_path, live_capture_path):
    match_result = match_faces(id_photo_path, live_capture_path)
    liveness_result = basic_liveness_check(live_capture_path)
    return {"face_match": match_result, "liveness": liveness_result}


if __name__ == "__main__":
    print(run_face_verification("sample_images/sample_id.jpg", "sample_images/sample_selfie.jpg"))
