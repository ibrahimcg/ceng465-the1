import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# MongoDB settings
MONGO_URI= os.getenv('MONGO_URI')

# JWT settings
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')  # Change in production
JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 24 hours

# Flask settings
DEBUG = os.getenv('DEBUG', 'True') == 'True'