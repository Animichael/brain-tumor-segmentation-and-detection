"""Landing page routes."""
from flask import Blueprint, render_template

from app.models import Patient, Prediction, Scan, SliderImage, Testimonial

main_bp = Blueprint("main", __name__)

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
    slides = (
        SliderImage.query.filter_by(is_active=True)
        .order_by(SliderImage.sort_order.asc())
        .all()
    )
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
