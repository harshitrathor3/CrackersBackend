from motor import motor_asyncio
from config import MONGODB_CONNECTION_STRING

client = motor_asyncio.AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
db = client["crackers_db"]
