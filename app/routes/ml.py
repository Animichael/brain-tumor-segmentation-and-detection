"""Run the classification + segmentation pipeline on an uploaded MRI scan
and show the result immediately, without persisting the image or any
patient / scan / prediction records.

The upload is processed inside a temporary directory that is deleted as
soon as the request finishes, and the segmented overlay is handed back to
the template as an inline base64 data URI - so nothing is written under
app/static/uploads/ and nothing is written to the database.
"""
import base64
import os
import tempfile

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import login_required

from app.forms import ScanUploadForm
from app.ml.inference import is_likely_mri, run_full_pipeline

ml_bp = Blueprint("ml", __name__, url_prefix="/ml")


def _image_data_uri(path):
    """Read an image file from disk and return it as a base64 data URI so
    the template can show it inline without it being saved under static/."""
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext or 'png'}"
    with open(path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


@ml_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    form = ScanUploadForm()
    if not form.validate_on_submit():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "error")
        return redirect(url_for("dashboard.scans"))

    file = form.scan_image.data
    ext = file.filename.rsplit(".", 1)[1].lower()

    # Everything below lives in a temp dir that is removed when the `with`
    # block exits - the upload, the segmented overlay, all of it.
    with tempfile.TemporaryDirectory() as work_dir:
        image_path = os.path.join(work_dir, f"scan.{ext}")
        segmented_path = os.path.join(work_dir, f"scan_segmented.{ext}")
        file.save(image_path)

        is_mri, reason = is_likely_mri(image_path)
        if not is_mri:
            flash(
                f"That upload was rejected: {reason}. "
                "Please upload an actual MRI scan image.",
                "error",
            )
            return redirect(url_for("dashboard.scans"))

        try:
            result = run_full_pipeline(image_path, segmented_path)
        except Exception:
            current_app.logger.exception("Inference failed")
            flash("Analysis failed for that image. Please try again.", "error")
            return redirect(url_for("dashboard.scans"))

        # Read the overlay back out while the temp dir still exists.
        segmented_data_uri = _image_data_uri(segmented_path)

    # Patient details are shown on the result page but never stored.
    patient = {
        "name": form.patient_name.data.strip(),
        "age": form.patient_age.data,
        "gender": form.patient_gender.data,
        "phone": form.patient_phone.data.strip() if form.patient_phone.data else None,
    }

    return render_template(
        "dashboard/result.html",
        patient=patient,
        result=result,
        segmented_data_uri=segmented_data_uri,
    )
