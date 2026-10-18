import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# Load environment variables from .env if present
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "campus_lost_and_found")
PORT = int(os.getenv("PORT", 5000))
SECRET_KEY = os.getenv("SECRET_KEY", "unifind-campus-secret-key-2026")

def get_mongo_client():
    """
    Establish a connection to MongoDB using PyMongo.
    Supports both local MongoDB and MongoDB Atlas (via TLS certifi).
    """
    options = {
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 10000,
    }
    
    # If connecting to MongoDB Atlas (+srv protocol or ssl/tls), pass certifi CA
    if "mongodb+srv://" in MONGO_URI or "ssl=true" in MONGO_URI.lower() or "tls=true" in MONGO_URI.lower():
        options["tlsCAFile"] = certifi.where()

    client = MongoClient(MONGO_URI, **options)
    return client

def get_database():
    """
    Returns the application's database instance.
    """
    client = get_mongo_client()
    return client[DB_NAME]
