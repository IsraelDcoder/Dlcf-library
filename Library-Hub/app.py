import os
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from dotenv import load_dotenv

from models import db

# Load environment variables
load_dotenv()

# Extensions
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def create_app():
    app = Flask(__name__)

    # -------------------------
    # Core Configuration
    # -------------------------
    app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB

    # -------------------------
    # Database Configuration
    # -------------------------
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # Fix Render postgres:// issue
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
    else:
        # Local fallback (development only)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        database_url = f"sqlite:///{os.path.join(base_dir, 'library.db')}"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    # -------------------------
    # Upload Configuration
    # -------------------------
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_root = os.path.join(base_dir, "uploads")

    app.config["UPLOAD_FOLDER"] = upload_root
    app.config["MAX_COMMUNITY_PHOTO_SIZE"] = 2 * 1024 * 1024
    app.config["COMMUNITY_PHOTO_THUMB_SIZE"] = (300, 300)

    # Ensure folders exist (NOTE: ephemeral on Render Free)
    folders = [
        "pdfs", "ebooks", "audio", "videos",
        "profiles", "communities", "live"
    ]
    for folder in folders:
        os.makedirs(os.path.join(upload_root, folder), exist_ok=True)

    # -------------------------
    # Initialize Extensions
    # -------------------------
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # -------------------------
    # Redis (Optional, for SocketIO scaling)
    # -------------------------
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        socketio.init_app(app, message_queue=redis_url)
    else:
        socketio.init_app(app)

    # -------------------------
    # User Loader
    # -------------------------
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------------------------
    # Blueprints
    # -------------------------
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.content import content_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.community import community_bp
    from routes.main_uploads import main_uploads

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(content_bp, url_prefix="/content")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(community_bp, url_prefix="/community")
    app.register_blueprint(main_uploads)

    # Optional live routes
    try:
        from routes.live import live_bp
        app.register_blueprint(live_bp, url_prefix="/live")
    except Exception as e:
        print("Live module not loaded:", e)

    # SocketIO handlers (optional)
    try:
        from routes.community import init_socketio
        init_socketio(socketio)
    except Exception as e:
        print("SocketIO handlers not loaded:", e)

    # -------------------------
    # Health Check (Render)
    # -------------------------
    @app.route("/healthz")
    def healthz():
        return jsonify(status="ok"), 200

    # -------------------------
    # Secure Admin Bootstrap
    # -------------------------
    with app.app_context():
        create_default_admin()

    return app


def create_default_admin():
    from models import User

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    # Do nothing unless explicitly configured
    if not admin_email or not admin_password:
        return

    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name="Admin",
            email=admin_email,
            role="admin"
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()


# Application instance (used by Gunicorn)
app = create_app()

# Local development only
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_ENV") != "production"
    )
