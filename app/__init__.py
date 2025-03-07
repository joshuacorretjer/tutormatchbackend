from flask import Flask
from .extensions import db, migrate
from .models import *  # Import your models
from .routes import main_routes  # Import the blueprint

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register the blueprint
    app.register_blueprint(main_routes)

    return app