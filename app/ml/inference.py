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
# is_likely_mri): real MRI slices scored under 3, ordinary photos over 20.
MRI_COLOR_SPREAD_THRESHOLD = 12.0

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


def is_likely_mri(image_path):
    """Coarse screen for "is this even an MRI-style scan," run before the
    classifier so an obviously-wrong upload gets a clear message instead of a
    confident-looking but meaningless prediction.

    MRI slices carry no color channel, so once exported to PNG/JPEG they come
    out with R, G and B nearly identical at every pixel (aside from a little
    JPEG chroma-subsampling noise). An ordinary photo - a phone snapshot, a
    screenshot, a document - almost never does. Checked against this app's
    own sample scans and stock photos, real MRI slices scored under 3 on the
    per-pixel |R-G|+|G-B|+|R-B| average; ordinary photos started above 20 -
    a wide, comfortable gap either side of the threshold below.

    This is a coarse gate, not a trained classifier: it catches color photos
    and screenshots, but can't catch a grayscale image of the wrong subject
    (e.g. a chest X-ray), since nothing in the pixel data alone distinguishes
    that from a valid brain slice.

    Returns (True, None) if it passes, or (False, reason) if it doesn't.
    """
    image = Image.open(image_path).convert("RGB")
    pixels = np.array(image, dtype=np.float32)
    r, g, b = pixels[..., 0], pixels[..., 1], pixels[..., 2]
    channel_spread = float(np.mean(np.abs(r - g) + np.abs(g - b) + np.abs(r - b)))

    if channel_spread <= MRI_COLOR_SPREAD_THRESHOLD:
        return True, None
    return False, "the image appears to be a color photo, not a grayscale MRI scan"


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
