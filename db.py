import pymongo
from config import MONGODB_CONNECTION_STRING


client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = client["crackers_db"]



