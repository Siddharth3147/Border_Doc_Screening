"""
ela_check.py

ELA = Error Level Analysis. Detects pixel-level tampering by re-saving
the image at a fixed JPEG quality and measuring the difference from
the original - edited regions compress differently than untouched ones.

--- IMPORTANT FIX vs the first version of this project ---
Plain ELA lights up EVERY text edge in the image (because text edges
always compress a bit differently than flat backgrounds), not just
edited regions. That gave a lot of false alarms on genuine documents
which are full of text.

Fix: instead of judging the whole image by one average brightness, we
split the image into a grid of blocks, measure each block's ELA
intensity, and only flag blocks that are a statistical OUTLIER
compared to the rest of the document (i.e. clearly brighter than the
general "this document has text everywhere" baseline). This way,
normal printed text stays background noise, and only a genuinely
tampered patch (like a swapped photo or edited digits) stands out.
"""

from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import cv2

GRID_SIZE = 20          # image is split into GRID_SIZE x GRID_SIZE blocks
Z_SCORE_THRESHOLD = 2.5  # how many std-devs above average counts as "suspicious"


def generate_ela_image(image_path, quality=90, save_path="ela_output.jpg"):
    original = Image.open(image_path).convert("RGB")

    temp_path = "temp_resaved.jpg"
    original.save(temp_path, "JPEG", quality=quality)
    resaved = Image.open(temp_path)

    diff = ImageChops.difference(original, resaved)

    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema]) or 1
    scale = 255.0 / max_diff
    diff = ImageEnhance.Brightness(diff).enhance(scale)
    diff.save(save_path)

    return save_path, diff


def analyze_blocks(diff_image):
    """
    Splits the ELA diff image into a grid and returns the mean
    intensity of each block, plus which blocks are statistical
    outliers (likely tampered regions).
    """
    arr = np.array(diff_image.convert("L")).astype(np.float32)
    h, w = arr.shape

    block_h = max(1, h // GRID_SIZE)
    block_w = max(1, w // GRID_SIZE)

    block_means = []
    block_coords = []

    for y in range(0, h, block_h):
        for x in range(0, w, block_w):
            block = arr[y:y + block_h, x:x + block_w]
            if block.size == 0:
                continue
            block_means.append(float(np.mean(block)))
            block_coords.append((x, y, block_w, block_h))

    block_means = np.array(block_means)
    global_mean = np.mean(block_means)
    global_std = np.std(block_means) if np.std(block_means) > 0 else 1

    flagged_blocks = []
    for i, mean_val in enumerate(block_means):
        z_score = (mean_val - global_mean) / global_std
        if z_score > Z_SCORE_THRESHOLD:
            flagged_blocks.append(block_coords[i])

    outlier_ratio = len(flagged_blocks) / len(block_means) if len(block_means) else 0
    return flagged_blocks, outlier_ratio


def draw_flagged_overlay(image_path, flagged_blocks, save_path="ela_overlay.jpg"):
    """
    Draws red boxes ONLY around the suspicious outlier blocks, on top
    of the original document image - much clearer for a reviewer than
    a heatmap that lights up all the text.
    """
    img = cv2.imread(image_path)
    for (x, y, bw, bh) in flagged_blocks:
        cv2.rectangle(img, (x, y), (x + bw, y + bh), (0, 0, 255), 2)
    cv2.imwrite(save_path, img)
    return save_path


def run_ela(image_path):
    diff_save_path, diff_img = generate_ela_image(image_path)
    flagged_blocks, outlier_ratio = analyze_blocks(diff_img)
    overlay_path = draw_flagged_overlay(image_path, flagged_blocks)

    # score = percentage of the document that looks anomalous (0-100)
    score = round(min(100, outlier_ratio * 100 * 4), 0)  # scaled up a bit, outliers are naturally rare

    return {
        "ela_heatmap_path": diff_save_path,
        "ela_overlay_path": overlay_path,
        "flagged_block_count": len(flagged_blocks),
        "ela_score": int(score),
        "flag": len(flagged_blocks) > 3  # a handful of scattered outliers is normal noise; a cluster is not
    }


if __name__ == "__main__":
    result = run_ela("sample_images/sample_id.jpg")
    print(result)
