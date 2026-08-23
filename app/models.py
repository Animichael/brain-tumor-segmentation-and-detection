from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Application user account (admin/doctor/user)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # admin / doctor / user
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    patients_created = db.relationship("Patient", backref="creator", lazy=True)
    scans_uploaded = db.relationship("Scan", backref="uploader", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class SliderImage(db.Model):
    """CMS-managed hero slider image shown on the landing page."""

    __tablename__ = "slider_images"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300), nullable=True)
    image_filename = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f"<SliderImage {self.title}>"


class Patient(db.Model):
    """A patient record on whom scans are performed."""

    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    scans = db.relationship("Scan", backref="patient", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient {self.name}>"


class Scan(db.Model):
    """An uploaded MRI scan belonging to a patient."""

    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    segmented_filename = db.Column(db.String(255), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending / processed
    created_at = db.Column(db.DateTime, default=utcnow)

    prediction = db.relationship(
        "Prediction", backref="scan", uselist=False, lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Scan {self.id} patient={self.patient_id}>"


class Prediction(db.Model):
    """ResNet50 classification + tumor area result for a scan."""

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id"), nullable=False)
    classification = db.Column(db.String(50), nullable=False)  # Glioma/Meningioma/Pituitary/No Tumor
    confidence = db.Column(db.Float, nullable=False)
    tumor_area_percent = db.Column(db.Float, nullable=True)
    sequence_type = db.Column(db.String(30), nullable=True)  # Estimated MRI sequence, e.g. "T1-weighted"
    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f"<Prediction {self.classification} ({self.confidence:.2f})>"


class Testimonial(db.Model):
    """Patient/doctor testimonial shown on the landing page."""

    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=True)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    avatar = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Testimonial {self.name}>"
