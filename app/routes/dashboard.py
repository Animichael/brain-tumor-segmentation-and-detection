"""Dashboard pages: overview, scans, results, hero-slider CMS, profile."""
import math
import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.decorators import admin_required
from app.forms import DeleteForm, ProfileForm, ScanUploadForm
from app.models import Patient, Prediction, Scan, User
from app.routes.main import _hero_slides

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

PER_PAGE = 8

# Validated categorical palette (dataviz skill's documented default, first 4
# slots) — passes the adjacent CVD/contrast checks in both light and dark mode.
CLASSIFICATION_ORDER = ["Glioma", "Meningioma", "Pituitary", "No Tumor"]

DONUT_RADIUS = 64
DONUT_STROKE = 20
DONUT_CENTER = 90
DONUT_LABEL_RADIUS = DONUT_RADIUS + DONUT_STROKE / 2 + 12
DONUT_GAP_PX = 3


def _build_classification_donut():
    """Segment geometry for an SVG donut, computed server-side so the template
    stays pure markup (no trig in Jinja)."""
    rows = (
        db.session.query(Prediction.classification, db.func.count(Prediction.id))
        .group_by(Prediction.classification)
        .all()
    )
    counts = dict(rows)
    total = sum(counts.values())
    circumference = 2 * math.pi * DONUT_RADIUS

    segments = []
    cumulative_fraction = 0.0
    for index, classification in enumerate(CLASSIFICATION_ORDER, start=1):
        count = counts.get(classification, 0)
        if not count:
            continue
        fraction = count / total
        length = max(fraction * circumference - DONUT_GAP_PX, 0)
        mid_angle = (cumulative_fraction + fraction / 2) * 2 * math.pi - math.pi / 2
        segments.append(
            {
                "slot": index,
                "label": classification,
                "count": count,
                "percent": round(fraction * 100),
                "dasharray": f"{length:.2f} {circumference:.2f}",
                "dashoffset": f"{-(cumulative_fraction * circumference):.2f}",
                "label_x": round(DONUT_CENTER + DONUT_LABEL_RADIUS * math.cos(mid_angle), 1),
                "label_y": round(DONUT_CENTER + DONUT_LABEL_RADIUS * math.sin(mid_angle), 1),
            }
        )
        cumulative_fraction += fraction

    return {
        "segments": segments,
        "total": total,
        "center": DONUT_CENTER,
        "radius": DONUT_RADIUS,
        "stroke": DONUT_STROKE,
    }


def _build_status_split():
    processed = Scan.query.filter_by(status="processed").count()
    pending = Scan.query.filter_by(status="pending").count()
    total = processed + pending
    return {
        "processed": processed,
        "pending": pending,
        "total": total,
        "processed_percent": round(processed / total * 100) if total else 0,
        "pending_percent": round(pending / total * 100) if total else 0,
    }


@dashboard_bp.route("/")
@login_required
def index():
    stats = {
        "patients": Patient.query.count(),
        "scans": Scan.query.count(),
        "processed": Scan.query.filter_by(status="processed").count(),
        "predictions": Prediction.query.count(),
    }
    recent_scans = Scan.query.order_by(Scan.created_at.desc()).limit(5).all()
    donut = _build_classification_donut()
    status_split = _build_status_split()
    return render_template(
        "dashboard/index.html",
        stats=stats,
        recent_scans=recent_scans,
        donut=donut,
        status_split=status_split,
    )


@dashboard_bp.route("/scans")
@login_required
def scans():
    latest_id = request.args.get("latest", type=int)
    latest_scan = None
    if latest_id:
        latest_scan = Scan.query.get(latest_id)
    if latest_scan is None:
        latest_scan = Scan.query.order_by(Scan.created_at.desc()).first()

    upload_form = ScanUploadForm()
    return render_template("dashboard/scans.html", latest_scan=latest_scan, upload_form=upload_form)


@dashboard_bp.route("/results")
@login_required
def results():
    page = request.args.get("page", 1, type=int)
    pagination = Prediction.query.order_by(Prediction.created_at.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    delete_form = DeleteForm()
    return render_template("dashboard/results.html", pagination=pagination, delete_form=delete_form)


@dashboard_bp.route("/results/<int:prediction_id>/delete", methods=["POST"])
@login_required
def delete_result(prediction_id):
    form = DeleteForm()
    if not form.validate_on_submit():
        flash("Could not delete that record. Please try again.", "error")
        return redirect(url_for("dashboard.results"))

    prediction = Prediction.query.get_or_404(prediction_id)
    scan = prediction.scan

    upload_dir = current_app.config["UPLOAD_FOLDER_SCANS"]
    for filename in (scan.image_filename, scan.segmented_filename):
        if not filename:
            continue
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    db.session.delete(scan)
    db.session.commit()

    flash("Scan result deleted.", "success")
    page = request.args.get("page", type=int)
    return redirect(url_for("dashboard.results", page=page) if page else url_for("dashboard.results"))


@dashboard_bp.route("/slider")
@login_required
@admin_required
def slider():
    slides = _hero_slides()
    return render_template("dashboard/slider.html", slides=slides)


@dashboard_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("dashboard.profile"))

        email = form.email.data.strip().lower()
        if email != current_user.email and User.query.filter(User.email == email, User.id != current_user.id).first():
            flash("That email is already in use by another account.", "error")
            return redirect(url_for("dashboard.profile"))

        current_user.full_name = form.full_name.data.strip()
        current_user.email = email
        if form.new_password.data:
            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("dashboard.profile"))

    return render_template("dashboard/profile.html", form=form)
