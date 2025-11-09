import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Initialize extensions globally (will be attached to app later)
db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    """Flask application factory"""
    app = Flask(__name__)

    # Basic configuration
    app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_123')
    
    # Configure SQLite database with absolute path
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'users.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Configure uploads folder
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Configure max content length for uploads (16MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints
    from .auth import auth_bp
    from .views import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')  # Auth routes under /auth/
    app.register_blueprint(main_bp)  # Main routes at root level

    # Create all database tables
    with app.app_context():
        db.create_all()

    return app
