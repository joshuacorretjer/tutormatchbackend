import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Flask-JWT-Extended settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    # Database settings
    SQLALCHEMY_DATABASE_URI = 'postgresql://tutormatch:password1234@localhost/tutormatch'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
