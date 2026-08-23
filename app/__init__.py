import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_class=Config):
    """Application factory for the Brain Cancer Detection app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_SCANS"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_SLIDER"], exist_ok=True)

    db.init_app(app)

    from app.icons import fluent_icon

    app.jinja_env.globals["icon"] = fluent_icon

    @app.context_processor
    def inject_current_year():
        from datetime import datetime

        return {"current_year": datetime.now().year}

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.main import main_bp
    from app.routes.ml import ml_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ml_bp)

    with app.app_context():
        db.create_all()

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed the database with demo admin, slider images, testimonials, patients, scans."""
        from app.seed import seed_database

        seed_database()

    return app
