"""
ai_generated_check.py

THIS is the module that uses actual, genuine AI (deep learning) -
unlike the ELA/metadata/font checks which are rule-based heuristics.

We use a pretrained Vision Transformer model from Hugging Face
(Organika/sdxl-detector) that has been specifically trained on
thousands of real vs AI-generated (Stable Diffusion / Midjourney /
DALL-E etc.) images to learn the difference between them.

This directly answers the "Generative AI Detection" requirement from
the problem statement (SIH26188) - spotting documents that were
generated from scratch by diffusion models / LLM-based tools, rather
than scanned/photographed physical documents.

How it works (in simple terms):
- The model looks at texture patterns, color distributions, and
  frequency artifacts that diffusion models tend to leave behind,
  which are usually invisible to the human eye but detectable by a
  neural network trained on thousands of examples.

NOTE: First time this runs, it needs internet to download the model
weights (roughly 300-400 MB, one-time only). After that it works
without internet. If the required libraries (torch/transformers)
aren't installed, this check is skipped gracefully and the rest of
the app still works - see requirements.txt for how to enable it.
"""

import functools

MODEL_NAME = "Organika/sdxl-detector"

_import_error_message = None

try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    _TRANSFORMERS_AVAILABLE = False
    _import_error_message = str(e)


@functools.lru_cache(maxsize=1)
def _get_classifier():
    """
    Loading a deep learning model takes a few seconds, so we cache it
    and only load it once per app run instead of every single scan.
    """
    return pipeline("image-classification", model=MODEL_NAME)


def run_ai_generated_check(image_path):
    """
    Runs the image through the pretrained model and returns whether
    it thinks the image is AI-generated, along with a confidence score.
    """
    if not _TRANSFORMERS_AVAILABLE:
        return {
            "available": False,
            "is_ai_generated": False,
            "confidence": 0,
            "raw_results": [],
            "error": (
                "AI-generation detection is disabled because 'transformers' "
                "and 'torch' are not installed. Run: pip install torch transformers"
            )
        }

    try:
        classifier = _get_classifier()
        results = classifier(image_path)
        # results looks like: [{'label': 'artificial', 'score': 0.91}, {'label': 'human', 'score': 0.09}]

        top_result = max(results, key=lambda r: r["score"])
        label_lower = top_result["label"].lower()

        ai_keywords = ["artificial", "ai", "fake", "generated", "synthetic"]
        is_ai_generated = any(keyword in label_lower for keyword in ai_keywords)

        return {
            "available": True,
            "is_ai_generated": is_ai_generated,
            "confidence": round(top_result["score"] * 100, 2),
            "raw_results": results,
            "error": None
        }

    except Exception as e:
        return {
            "available": True,
            "is_ai_generated": False,
            "confidence": 0,
            "raw_results": [],
            "error": str(e)
        }


if __name__ == "__main__":
    result = run_ai_generated_check("sample_images/sample_id.jpg")
    print(result)
