from motor import motor_asyncio
from config import MONGODB_CONNECTION_STRING, DB_NAME

client = motor_asyncio.AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
db = client[DB_NAME]
