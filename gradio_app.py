"""Gradio entrypoint for the Hugging Face Space.

A thin demo wrapper around the same ML pipeline the Flask app uses
(app/ml/inference.py): upload a brain MRI slice, get back the tumour
classification, model confidence, estimated tumour area, an estimated MRI
sequence type, and a highlighted segmentation overlay.

The full Flask app (accounts, patient records, dashboard) is unchanged in
the repo - it just isn't what runs on the Space, because Hugging Face only
offers Docker Spaces on a paid plan. This file is named gradio_app.py
(not app.py) so it doesn't collide with the app/ package.
"""
import os
import tempfile

import gradio as gr

from app.ml.inference import is_likely_mri, run_full_pipeline

TITLE = "NeuroScan AI - Brain Tumour Detection & Segmentation"

DESCRIPTION = """
Upload a single brain **MRI slice** (PNG or JPG). The app runs a ResNet-50
tumour classifier and a YOLOv11 segmentation model, then returns the
predicted tumour type, the model's confidence, an estimated tumour area, an
estimated MRI sequence, and an image with the tumour region highlighted.

*Educational demo built for research coursework - not a medical device and
not for clinical use. The first analysis after the Space wakes up takes
1-2 minutes while the models download; later ones are fast.*
"""

CLASS_BLURB = {
    "Glioma": "A tumour arising from glial cells; the most common primary brain tumour.",
    "Meningioma": "A usually benign tumour of the meninges (the brain's outer membranes).",
    "Pituitary": "A tumour of the pituitary gland at the base of the brain.",
    "No Tumor": "No tumour detected in this slice.",
}


def analyze(image_path):
    """Run the full pipeline on one uploaded image and return
    (overlay_image_path, {label: confidence}, markdown_summary)."""
    if not image_path:
        raise gr.Error("Please upload an MRI image first.")

    is_mri, reason = is_likely_mri(image_path)
    if not is_mri:
        raise gr.Error(f"That image was rejected: {reason}. Please upload an actual MRI scan.")

    ext = os.path.splitext(image_path)[1].lstrip(".").lower() or "png"
    out_dir = tempfile.mkdtemp()
    overlay_path = os.path.join(out_dir, f"segmented.{ext}")

    result = run_full_pipeline(image_path, overlay_path)

    label = result["classification"]
    confidence = float(result["confidence"])
    summary = (
        f"### {label}\n"
        f"{CLASS_BLURB.get(label, '')}\n\n"
        f"- **Confidence:** {confidence * 100:.1f}%\n"
        f"- **Estimated tumour area:** {result['tumor_area_percent']}% of the image\n"
        f"- **Estimated MRI sequence:** {result['sequence_type'] or 'Undetermined'} *(rough heuristic)*\n"
    )
    return overlay_path, {label: confidence}, summary


with gr.Blocks(title=TITLE) as demo:
    gr.Markdown(f"# {TITLE}")
    gr.Markdown(DESCRIPTION)

    with gr.Row():
        with gr.Column():
            image_in = gr.Image(type="filepath", label="MRI scan (PNG / JPG)")
            run_btn = gr.Button("Analyze scan", variant="primary")
        with gr.Column():
            overlay_out = gr.Image(label="Segmentation overlay")
            label_out = gr.Label(label="Classification", num_top_classes=1)
            summary_out = gr.Markdown()

    run_btn.click(analyze, inputs=image_in, outputs=[overlay_out, label_out, summary_out])

    gr.Markdown(
        "Models: `prithivMLmods/BrainTumor-Classification-Mini` (classification) and "
        "`sajjadhadi/YOLOv11-Tumor-Detection` (segmentation)."
    )

if __name__ == "__main__":
    demo.launch()
