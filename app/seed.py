"""One-time database seeding: admin user, hero slider images, testimonials,
and sample patients/scans/predictions so the dashboard has real records to
render before the ML pipeline and CMS forms are built out in later steps.
"""
from app import db
from app.models import Patient, Prediction, Scan, SliderImage, Testimonial, User

SLIDES = [
    {
        "title": "Advanced MRI Diagnostics",
        "subtitle": "State-of-the-art imaging technology for early, accurate brain tumor detection.",
        "image_filename": "slide-1-mri-machine.jpg",
        "sort_order": 1,
    },
    {
        "title": "Precision-Guided Neurosurgery",
        "subtitle": "Expert surgical teams supported by AI-assisted tumor localization.",
        "image_filename": "slide-2-surgical-team.jpg",
        "sort_order": 2,
    },
    {
        "title": "AI-Powered Tumor Segmentation",
        "subtitle": "Deep learning models trained to classify and segment brain scans in seconds.",
        "image_filename": "slide-3-brain-scan.jpg",
        "sort_order": 3,
    },
]

TESTIMONIALS = [
    {
        "name": "Dr. Sarah Whitfield",
        "role": "Consultant Neuroradiologist",
        "message": "The segmentation accuracy has noticeably shortened our review time on ambiguous scans.",
        "rating": 5,
    },
    {
        "name": "Michael Owusu",
        "role": "Patient",
        "message": "The whole process felt fast and the reports were easy to understand.",
        "rating": 5,
    },
    {
        "name": "Dr. Amara Chen",
        "role": "Oncology Surgeon",
        "message": "Having a confidence score alongside the classification helps us triage cases faster.",
        "rating": 4,
    },
    {
        "name": "Priya Nair",
        "role": "Patient",
        "message": "Clear communication throughout and a reassuring, professional experience.",
        "rating": 5,
    },
]

PATIENTS = [
    {"name": "John Doe", "age": 45, "gender": "Male", "phone": "+1-555-0101"},
    {"name": "Jane Smith", "age": 32, "gender": "Female", "phone": "+1-555-0102"},
    {"name": "Ahmed Khan", "age": 58, "gender": "Male", "phone": "+1-555-0103"},
    {"name": "Maria Garcia", "age": 29, "gender": "Female", "phone": "+1-555-0104"},
]

# (patient_index, image_filename, segmented_filename, status, prediction)
# prediction = (classification, confidence, tumor_area_percent) or None
SCANS = [
    (0, "scan_sample_1.jpg", "scan_sample_1_segmented.jpg", "processed", ("Glioma", 0.94, 6.8)),
    (0, "scan_sample_2.jpg", "scan_sample_2_segmented.jpg", "processed", ("Meningioma", 0.88, 4.2)),
    (1, "scan_sample_3.jpg", "scan_sample_3_segmented.jpg", "processed", ("Pituitary", 0.91, 3.1)),
    (2, "scan_sample_4.jpg", "scan_sample_4_segmented.jpg", "processed", ("No Tumor", 0.97, 0.0)),
    (3, "scan_sample_2.jpg", None, "pending", None),
]


def seed_database():
    """Populate an empty database with demo records. Safe to call multiple times."""
    if User.query.first():
        print("Database already contains data — skipping seed.")
        return

    admin = User(
        full_name="System Administrator",
        email="admin@braincancerapp.com",
        role="admin",
    )
    admin.set_password("Admin@123")
    db.session.add(admin)
    db.session.flush()  # assign admin.id before it's referenced as a foreign key

    for slide in SLIDES:
        db.session.add(SliderImage(is_active=True, **slide))

    for testimonial in TESTIMONIALS:
        db.session.add(Testimonial(**testimonial))

    patients = []
    for patient_data in PATIENTS:
        patient = Patient(created_by=admin.id, **patient_data)
        patients.append(patient)
        db.session.add(patient)

    db.session.flush()  # assign patient ids before scans reference them

    for patient_index, image_filename, segmented_filename, status, prediction in SCANS:
        scan = Scan(
            patient_id=patients[patient_index].id,
            image_filename=image_filename,
            segmented_filename=segmented_filename,
            uploaded_by=admin.id,
            status=status,
        )
        db.session.add(scan)
        db.session.flush()

        if prediction:
            classification, confidence, tumor_area_percent = prediction
            db.session.add(
                Prediction(
                    scan_id=scan.id,
                    classification=classification,
                    confidence=confidence,
                    tumor_area_percent=tumor_area_percent,
                )
            )

    db.session.commit()
    print("Database seeded: 1 admin, 3 slides, 4 testimonials, 4 patients, 5 scans, 4 predictions.")
