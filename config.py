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
    SQLALCHEMY_DATABASE_URI = 'os.environ.get("DATABASE_URL")'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask Mail Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'tutormatch.test@gmail.com'
    MAIL_PASSWORD = 'spni opwe lano ystk'
