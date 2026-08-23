"""Landing page routes."""
import os

from flask import Blueprint, current_app, render_template

from app.models import Patient, Prediction, Scan, Testimonial

main_bp = Blueprint("main", __name__)

HERO_SLIDE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _hero_slides():
    """Hero slider images, read directly from disk rather than the
    database - these are static marketing assets shipped with the repo, not
    user-generated content, so there's nothing a database row adds here
    except another thing that can be out of sync with what's actually on
    disk (or empty, on a fresh/unseeded database)."""
    upload_dir = current_app.config["UPLOAD_FOLDER_SLIDER"]
    if not os.path.isdir(upload_dir):
        return []
    return sorted(
        filename
        for filename in os.listdir(upload_dir)
        if os.path.splitext(filename)[1].lower() in HERO_SLIDE_EXTENSIONS
    )

HOW_IT_WORKS = [
    {
        "icon": "arrow-upload-24-regular",
        "title": "Upload MRI Scan",
        "description": "Enter the patient's details and upload a T1/T2 MRI slice through the secure dashboard.",
    },
    {
        "icon": "brain-circuit-24-regular",
        "title": "AI Analysis",
        "description": "The classification and segmentation models process the scan in seconds.",
    },
    {
        "icon": "scan-24-regular",
        "title": "Tumor Segmentation",
        "description": "Suspicious regions are highlighted directly on the MRI image.",
    },
    {
        "icon": "clipboard-checkmark-24-regular",
        "title": "Review Results",
        "description": "Clinicians review the classification, confidence score, and tumor area in the results table.",
    },
]

FEATURES = [
    {
        "icon": "flash-24-regular",
        "title": "Fast Turnaround",
        "description": "Get classification and segmentation results back in seconds, not days.",
    },
    {
        "icon": "shield-checkmark-24-regular",
        "title": "Secure & Private",
        "description": "Patient data and scans stay protected within your clinical workflow.",
    },
    {
        "icon": "clipboard-pulse-24-regular",
        "title": "Built for Clinicians",
        "description": "Designed around real diagnostic workflows, from intake to review.",
    },
]


@main_bp.route("/")
def index():
    slides = _hero_slides()
    testimonials = Testimonial.query.all()
    stats = [
        {"icon": "scan-24-regular", "value": str(Scan.query.count()), "label": "Scans Analyzed"},
        {"icon": "people-community-24-regular", "value": str(Patient.query.count()), "label": "Patients Served"},
        {"icon": "clipboard-pulse-24-regular", "value": str(Prediction.query.count()), "label": "AI Predictions"},
    ]
    return render_template(
        "landing.html",
        slides=slides,
        testimonials=testimonials,
        how_it_works=HOW_IT_WORKS,
        features=FEATURES,
        stats=stats,
    )
