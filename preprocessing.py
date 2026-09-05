"""
preprocessing.py

Basic image cleanup before we run any forensic checks on the document:
1. Denoise the image a little
2. Fix skew (if the document was photographed at an angle)

Border checkpoint documents are often scanned/photographed quickly
under bad lighting, so this step matters a lot for OCR accuracy later.
"""

import cv2
import numpy as np


def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image at {path}")
    return img


def denoise_image(img):
    return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)


def deskew_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return img

    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_CUBIC,
                           borderMode=cv2.BORDER_REPLICATE)


def preprocess_pipeline(path, save_path="preprocessed_output.jpg"):
    img = load_image(path)
    img = denoise_image(img)
    img = deskew_image(img)
    cv2.imwrite(save_path, img)
    return save_path


if __name__ == "__main__":
    out = preprocess_pipeline("sample_images/sample_id.jpg")
    print("Preprocessed image saved at:", out)
