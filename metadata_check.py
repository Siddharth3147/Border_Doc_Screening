"""
metadata_check.py

Checks EXIF metadata for signs of editing software (Photoshop, GIMP,
AI tools etc). Real scanned/camera-captured documents usually don't
carry these tags.
"""

from PIL import Image
from PIL.ExifTags import TAGS

SUSPICIOUS_SOFTWARE_KEYWORDS = [
    "photoshop", "gimp", "canva", "snapseed",
    "picsart", "lightroom", "midjourney",
    "dall-e", "stable diffusion", "diffusion"
]


def extract_metadata(image_path):
    image = Image.open(image_path)
    exif_data = {}
    raw_exif = image.getexif()
    if not raw_exif:
        return exif_data
    for tag_id, value in raw_exif.items():
        tag_name = TAGS.get(tag_id, tag_id)
        exif_data[tag_name] = value
    return exif_data


def check_metadata(image_path):
    metadata = extract_metadata(image_path)
    flagged = False
    reason = "No suspicious metadata found."
    software_tag = metadata.get("Software", "")

    if software_tag:
        software_lower = str(software_tag).lower()
        for keyword in SUSPICIOUS_SOFTWARE_KEYWORDS:
            if keyword in software_lower:
                flagged = True
                reason = f"Editing software detected in metadata: {software_tag}"
                break

    return {
        "metadata": metadata,
        "software_tag": software_tag,
        "flagged": flagged,
        "reason": reason,
        "metadata_missing": len(metadata) == 0
    }


if __name__ == "__main__":
    print(check_metadata("sample_images/sample_id.jpg"))
