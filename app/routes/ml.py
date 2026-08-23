"""Register a patient and run the classification + segmentation pipeline
on their uploaded MRI scan, in one combined submission."""
import os
import uuid

from flask import Blueprint, current_app, flash, redirect, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import ScanUploadForm
from app.ml.inference import is_likely_mri, run_full_pipeline
from app.models import Patient, Prediction, Scan

ml_bp = Blueprint("ml", __name__, url_prefix="/ml")


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
    upload_dir = current_app.config["UPLOAD_FOLDER_SCANS"]
    ext = file.filename.rsplit(".", 1)[1].lower()
    image_filename = f"{uuid.uuid4().hex}.{ext}"
    image_path = os.path.join(upload_dir, image_filename)
    file.save(image_path)

    is_mri, reason = is_likely_mri(image_path)
    if not is_mri:
        os.remove(image_path)
        flash(
            f"That upload was rejected: {reason}. Please upload an actual MRI scan image.",
            "error",
        )
        return redirect(url_for("dashboard.scans"))

    patient = Patient(
        name=form.patient_name.data.strip(),
        age=form.patient_age.data,
        gender=form.patient_gender.data,
        phone=form.patient_phone.data.strip() if form.patient_phone.data else None,
        address=form.patient_address.data.strip() if form.patient_address.data else None,
        created_by=current_user.id,
    )
    db.session.add(patient)
    db.session.flush()  # assign patient.id before the scan references it

    scan = Scan(
        patient_id=patient.id,
        image_filename=image_filename,
        uploaded_by=current_user.id,
        status="pending",
    )
    db.session.add(scan)
    db.session.commit()

    try:
        segmented_filename = f"{uuid.uuid4().hex}_segmented.{ext}"
        result = run_full_pipeline(
            os.path.join(upload_dir, image_filename),
            os.path.join(upload_dir, segmented_filename),
        )

        scan.segmented_filename = segmented_filename
        scan.status = "processed"
        db.session.add(
            Prediction(
                scan_id=scan.id,
                classification=result["classification"],
                confidence=result["confidence"],
                tumor_area_percent=result["tumor_area_percent"],
                sequence_type=result["sequence_type"],
            )
        )
        db.session.commit()
        flash(
            f"Scan analyzed: {result['classification']} "
            f"({result['confidence'] * 100:.0f}% confidence).",
            "success",
        )
    except Exception:
        current_app.logger.exception("Inference failed for scan %s", scan.id)
        flash("The scan was uploaded, but analysis failed. It has been saved as pending.", "error")

    return redirect(url_for("dashboard.scans", latest=scan.id))
