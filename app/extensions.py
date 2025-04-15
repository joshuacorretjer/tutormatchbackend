from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_mail import Mail

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize Flask-Migrate
migrate = Migrate()

# Initialize Flask-Login
login_manager = LoginManager()

# Initialize Flask-JWT-Manager
jwt = JWTManager()

# Initialize Flask-Mail
mail = Mail()