import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://tutormatch:password1234@localhost:5432/tutormatch_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False