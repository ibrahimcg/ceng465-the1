# database.py
from pymongo import MongoClient

# Initialize without connecting
mongo_client = None
db = None

def get_db():
    return db

def init_db(app):
    global mongo_client
    global db
    
    # Only establish connection once
    if mongo_client is None:
        mongo_client = MongoClient(app.config['MONGO_URI'])
        db = mongo_client.get_database("the1-database")
    
    return db