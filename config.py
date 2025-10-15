import os
from dotenv import load_dotenv


# Load .env variables
try:
    ENV = os.environ["ENV"]
except Exception as e:
    print("Using local ENVs:", e)
    load_dotenv('config.env')

# MongoDB
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
DB_NAME = os.getenv("DB_NAME", "crackers_db")

# Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Brevo
BREVO_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = "harshitrathorelink@gmail.com"
SENDER_NAME = "Harshit Rathore"
SUBJECT = "Your order is successfully placed!"


# Analytics
ANALYTICS_API = os.getenv("ANALYTICS_API")
