from flask import Flask
from .extensions import db, migrate, login_manager, jwt
from .models import *  # Import your models
from .routes import api_bp, main_routes  # Import the blueprints
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

    # Load configuration
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)

    # Register the Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')  # API routes under /api
    app.register_blueprint(main_routes)  # Main routes at the root

    return app