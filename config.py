import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

_database_url = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "app.db")
)
# Some providers (Render, Heroku) hand out "postgres://" URLs, but
# SQLAlchemy 1.4+/psycopg2 require the "postgresql://" scheme.
if _database_url.startswith("postgres://"):
    _database_url = _database_url.replace("postgres://", "postgresql://", 1)


class Config:
    """Base Flask configuration for the Brain Cancer Detection app."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Upload folders
    UPLOAD_FOLDER_SCANS = os.path.join(BASE_DIR, "app", "static", "uploads", "scans")
    UPLOAD_FOLDER_SLIDER = os.path.join(BASE_DIR, "app", "static", "uploads", "slider")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
