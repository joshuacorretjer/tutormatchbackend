from flask import Flask
from .extensions import db, migrate
from .models import *  # Import your models

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    return app