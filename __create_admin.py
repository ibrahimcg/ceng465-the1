from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)

db = client["the1-database"]

# Create admin user
admin_user = {
    'username': 'admin',
    'password': generate_password_hash('admin495'),  # Change this!
    'is_admin': True,
    'reviews': [],
    'average_rating': 0,
    'created_at': datetime.datetime.now()
}

# Check if admin exists
existing_admin = db.users.find_one({'username': 'admin'})

if existing_admin:
    print("Admin user already exists")
else:
    result = db.users.insert_one(admin_user)
    print(f"Admin user created with ID: {result.inserted_id}")