import os
from dotenv import load_dotenv


# Load .env variables
try:
    ENV = os.environ["ENV"]
except Exception as e:
    print("Using local ENVs:", e)
    load_dotenv('config.env')


MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")

