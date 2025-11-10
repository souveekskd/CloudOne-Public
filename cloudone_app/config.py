import os
from dotenv import load_dotenv

# Load .env file from the *root* directory (where run.py is)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class Config:
    """Base configuration."""
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
