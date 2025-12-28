import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_socketio import SocketIO

load_dotenv()

from models import db

migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    # Use DATABASE_URL from environment if provided, otherwise fall back to a local SQLite DB
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library.db')
        database_url = f"sqlite:///{db_file}"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    # Community photo constraints
    app.config['MAX_COMMUNITY_PHOTO_SIZE'] = 2 * 1024 * 1024  # 2 MB
    app.config['COMMUNITY_PHOTO_THUMB_SIZE'] = (300, 300)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    for folder in ['pdfs', 'ebooks', 'audio', 'videos', 'profiles', 'communities']:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    # folder for live session recordings
    live_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'live')
    if not os.path.exists(live_folder):
        os.makedirs(live_folder)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    # Configure Redis client if provided and pass message_queue to SocketIO for scaling
    redis_url = os.environ.get('REDIS_URL')
    app.redis = None
    if redis_url:
        try:
            import redis as _redis
            app.redis = _redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            # If redis is not available or fails to connect, leave app.redis as None
            print('Warning: Redis not available or failed to connect:', e)
    if redis_url:
        socketio.init_app(app, cors_allowed_origins='*', message_queue=redis_url)
    else:
        socketio.init_app(app, cors_allowed_origins='*')
    
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.content import content_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(content_bp, url_prefix='/content')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    from routes.community import community_bp
    app.register_blueprint(community_bp, url_prefix='/community')
    # Live sessions (real-time + recordings)
    try:
        from routes.live import live_bp
        app.register_blueprint(live_bp, url_prefix='/live')
    except Exception as e:
        print('Warning: live routes not available:', e)
    # register uploads serving route for user-uploaded files
    from routes.main_uploads import main_uploads
    app.register_blueprint(main_uploads)
    # Register SocketIO handlers for community module (if available)
    try:
        from routes.community import init_socketio
        init_socketio(socketio)
    except Exception as e:
        print('Warning: failed to initialize community socket handlers:', e)

    with app.app_context():
        db.create_all()
        create_default_admin()
    
    return app

def create_default_admin():
    from models import User
    admin = User.query.filter_by(email='admin@dlcf.org').first()
    if not admin:
        admin = User(
            name='Admin',
            email='admin@dlcf.org',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

app = create_app()

if __name__ == '__main__':
    # Use SocketIO runner for real-time features
    import webbrowser
    port = int(os.environ.get('PORT', '5000'))
    host = os.environ.get('HOST', '127.0.0.1')
    # Use a local, clickable host for display when binding to all interfaces
    display_host = '127.0.0.1' if host == '0.0.0.0' else host
    url = f"http://{display_host}:{port}/"
    print(f"Starting DLCF e-Library on {url} (eazy product)")
    if os.environ.get('AUTO_OPEN_BROWSER', '0') == '1' and display_host in ("127.0.0.1", "localhost"):
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            pass
    socketio.run(app, host=host, port=port, debug=True)
