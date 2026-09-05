"""
copy_move_check.py

Detects "copy-move forgery" - when someone copies a region of the
SAME image and pastes it elsewhere (a very common trick for forging
stamps/seals - copy a genuine stamp and paste it onto a different
page, or duplicate part of a signature).

Directly maps to the problem statement's "Stamp Forgery Detection"
requirement.

Method: ORB keypoint detection + feature matching within the same
image. If we find clusters of keypoints that match each other very
closely (and are not just next to each other, which would be normal
repeating texture), it suggests a duplicated region.
"""

import cv2
import numpy as np


def detect_copy_move(image_path, min_matches=8, min_distance_px=40):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=1500)
    keypoints, descriptors = orb.detectAndCompute(gray, None)

    if descriptors is None or len(keypoints) < 20:
        return {
            "suspicious_pairs": 0,
            "flag": False,
            "reason": "Not enough features detected to run this check."
        }

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(descriptors, descriptors, k=2)

    suspicious_pairs = 0
    for match_pair in matches:
        if len(match_pair) < 2:
            continue
        m, n = match_pair
        # skip a keypoint matching itself
        if m.queryIdx == m.trainIdx:
            continue
        # a good, distinct match (not a random weak match)
        if m.distance < 0.7 * (n.distance + 1e-6):
            pt1 = np.array(keypoints[m.queryIdx].pt)
            pt2 = np.array(keypoints[m.trainIdx].pt)
            distance_apart = np.linalg.norm(pt1 - pt2)
            # far apart in the image = might be a real duplicated region,
            # not just texture right next to itself
            if distance_apart > min_distance_px:
                suspicious_pairs += 1

    flagged = suspicious_pairs > min_matches
    reason = (
        f"Found {suspicious_pairs} closely-matching duplicated feature pairs "
        "far apart in the document - possible copy-paste forgery (e.g. stamp/signature)."
        if flagged else
        "No significant duplicated regions detected."
    )

    return {
        "suspicious_pairs": suspicious_pairs,
        "flag": flagged,
        "reason": reason
    }


if __name__ == "__main__":
    print(detect_copy_move("sample_images/sample_id.jpg"))
