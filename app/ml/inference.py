"""Inference pipeline: brain MRI classification + tumor segmentation.

Both stages use real pretrained models pulled from the Hugging Face Hub on
first use and cached in memory for the life of the process:

- Classification: a ResNet50 fine-tuned on the standard 4-class brain tumor
  MRI dataset (glioma / meningioma / pituitary / no tumor).
- Segmentation: a YOLOv11-seg model fine-tuned to localize tumor regions,
  used to paint the red overlay and estimate tumor area.
"""
import numpy as np
from PIL import Image

CLASSIFIER_REPO = "prithivMLmods/BrainTumor-Classification-Mini"
SEGMENTER_REPO = "sajjadhadi/YOLOv11-Tumor-Detection"
SEGMENTER_FILE = "weights/best.pt"

# The classifier's own labels ("No Tumor", "Glioma", "Meningioma", "Pituitary")
# already match the app's schema; this just guards against casing variants.
CLASS_LABEL_MAP = {
    "glioma": "Glioma",
    "meningioma": "Meningioma",
    "no tumor": "No Tumor",
    "notumor": "No Tumor",
    "pituitary": "Pituitary",
}

OVERLAY_COLOR = np.array([220, 38, 38])  # matches the app's --color-danger red
OVERLAY_ALPHA = 0.45

# Calibrated against this app's own sample scans vs. its stock photos (see
# is_likely_mri): real MRI slices - including a sepia/warm-tinted one, the
# case that motivated this metric - scored at least 0.90; ordinary photos
# topped out at 0.62. Wide margin either side of the threshold below.
MRI_BORDER_UNIFORMITY_THRESHOLD = 0.75

# Real MRI slices never have much near-white area (max seen: 1.3%) - even a
# scan with almost no black background is still mid-gray tissue, not flat
# white. UI screenshots and documents are the opposite: mostly white page/
# background.
MRI_LIGHT_FRACTION_THRESHOLD = 0.3

_classifier = None
_segmenter = None


def _get_classifier():
    """Lazily load and cache the ResNet50 classification pipeline."""
    global _classifier
    if _classifier is None:
        from transformers import pipeline

        _classifier = pipeline("image-classification", model=CLASSIFIER_REPO)
    return _classifier


def _get_segmenter():
    """Lazily load and cache the YOLOv11-seg tumor segmentation model."""
    global _segmenter
    if _segmenter is None:
        from huggingface_hub import hf_hub_download
        from ultralytics import YOLO

        weights_path = hf_hub_download(SEGMENTER_REPO, SEGMENTER_FILE)
        _segmenter = YOLO(weights_path)
    return _segmenter


def _border_uniformity(gray_pixels):
    """Fraction of the image's outer border that clusters around a single
    dominant gray value.

    A scan image - MRI, CT, PET, any tint or color-mapping included - is a
    roughly circular/oval cross-section on a plain background that doesn't
    fill the rectangular frame, so its border is overwhelmingly one value
    (almost always black). An ordinary photo of a room, a person, or
    equipment has real content running edge to edge, so its border is a mix
    of many different values. This holds regardless of color tint, which is
    what makes it more reliable than checking color directly: a sepia-toned
    scan of old film still has a uniform border once converted to grayscale,
    even though its color channels alone look nothing like a neutral image.
    """
    height, width = gray_pixels.shape
    border_width = max(int(min(height, width) * 0.06), 3)
    border = np.concatenate(
        [
            gray_pixels[:border_width, :].ravel(),
            gray_pixels[-border_width:, :].ravel(),
            gray_pixels[:, :border_width].ravel(),
            gray_pixels[:, -border_width:].ravel(),
        ]
    )
    hist, edges = np.histogram(border, bins=32, range=(0, 255))
    mode_value = (edges[np.argmax(hist)] + edges[np.argmax(hist) + 1]) / 2
    return float((np.abs(border - mode_value) < 20).mean())


def is_likely_mri(image_path):
    """Coarse screen for "is this even an MRI-style scan," run before the
    classifier so an obviously-wrong upload gets a clear message instead of a
    confident-looking but meaningless prediction.

    Two checks, both grounded in how scan images actually look once exported
    to PNG/JPEG, calibrated against this app's own sample scans and stock
    photos with a comfortable margin either side:

    1. Border uniformity - see _border_uniformity. Real scans scored at
       least 0.90 here; ordinary photos topped out at 0.62. An earlier
       version of this check looked at color instead (MRI has no color
       channel) and rejected a real, legitimate scan that happened to be a
       sepia-toned scan of old film - color varies too much across
       legitimately-valid scans (tinted film, PET/SPECT color mapping) to be
       a safe signal. Border shape doesn't have that problem.
    2. Near-white area. A flat white background is essentially never part of
       a real scan - even one with almost no black margin is still mid-gray
       tissue, not white. Real slices had at most 1.3% near-white pixels; a
       screenshot of this app's own light-themed UI had 78%.

    This is a coarse gate, not a trained classifier: it catches photos,
    screenshots and documents, but can't catch a grayscale image of the
    wrong subject (e.g. a chest X-ray) framed the same way as a brain scan.

    Returns (True, None) if it passes, or (False, reason) if it doesn't.
    """
    image = Image.open(image_path).convert("RGB")
    pixels = np.array(image, dtype=np.float32)
    gray = pixels.mean(axis=2)

    light_fraction = float((gray > 235).mean())
    if light_fraction > MRI_LIGHT_FRACTION_THRESHOLD:
        return False, "the image looks like a screenshot or document, not an MRI scan"

    if _border_uniformity(gray) < MRI_BORDER_UNIFORMITY_THRESHOLD:
        return False, "the image doesn't have the framing of an MRI scan (a scan region on a plain background)"

    return True, None


def classify_scan(image_path):
    """Return (classification_label, confidence) for the given image."""
    classifier = _get_classifier()
    predictions = classifier(image_path)
    top = predictions[0]
    label = CLASS_LABEL_MAP.get(top["label"].lower(), top["label"])
    return label, float(top["score"])


def segment_scan(image_path, output_path):
    """Run tumor segmentation, save a red-overlay copy to output_path, and
    return the tumor area as a percentage of total image pixels."""
    segmenter = _get_segmenter()
    result = segmenter(image_path, verbose=False)[0]

    base = Image.open(image_path).convert("RGB")
    width, height = base.size

    if result.masks is None or len(result.masks.data) == 0:
        base.save(output_path)
        return 0.0

    combined_mask = np.zeros((height, width), dtype=bool)
    for mask_tensor in result.masks.data:
        mask = mask_tensor.cpu().numpy()
        mask_img = Image.fromarray((mask * 255).astype(np.uint8)).resize((width, height))
        combined_mask |= np.array(mask_img) > 127

    pixels = np.array(base).astype(np.float32)
    pixels[combined_mask] = (
        pixels[combined_mask] * (1 - OVERLAY_ALPHA) + OVERLAY_COLOR * OVERLAY_ALPHA
    )
    Image.fromarray(pixels.astype(np.uint8)).save(output_path)

    return round(float(combined_mask.sum()) / (width * height) * 100, 2)


def estimate_sequence_type(image_path):
    """Rough estimate of MRI sequence weighting (T1-weighted vs T2/FLAIR/other)
    from a single 2D slice.

    This is NOT a trained classifier — no reliable pretrained model or dataset
    exists for this from a plain JPEG/PNG (sequence type is normally read from
    DICOM metadata, which a JPEG upload doesn't carry). It's the classic
    textbook heuristic instead: CSF (the ventricles, near image center on a
    well-centered axial slice) reads dark on T1-weighted images and bright on
    T2-weighted images. It's a real, commonly-taught rule of thumb, but a
    coarse one — FLAIR also nulls CSF signal (looks dark, like T1), and
    off-center or non-axial slices break the assumption entirely. The UI
    labels this "estimated," never asserted as certain.
    """
    image = Image.open(image_path).convert("L")
    width, height = image.size
    pixels = np.array(image, dtype=np.float32)

    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = width / 2, height / 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    radius = min(width, height) * 0.08

    center_mask = dist <= radius
    tissue_mask = (dist > radius * 2) & (dist <= radius * 5)
    if not center_mask.any() or not tissue_mask.any():
        return None

    tissue_mean = float(pixels[tissue_mask].mean())
    if tissue_mean < 5:  # near-black background — nothing usable to compare
        return None

    ratio = float(pixels[center_mask].mean()) / tissue_mean
    if ratio < 0.7:
        return "T1-weighted"
    if ratio > 1.3:
        return "T2 / FLAIR / Other"
    return "Undetermined"


def run_full_pipeline(image_path, output_path):
    """Classify and segment a scan; returns a dict matching the Prediction model."""
    classification, confidence = classify_scan(image_path)
    tumor_area_percent = segment_scan(image_path, output_path)
    sequence_type = estimate_sequence_type(image_path)
    return {
        "classification": classification,
        "confidence": confidence,
        "tumor_area_percent": tumor_area_percent,
        "sequence_type": sequence_type,
    }
