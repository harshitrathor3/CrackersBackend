import traceback
from db import db
from bson import ObjectId



async def find_category_by_id(category_id):
    try:
        # Convert string to ObjectId
        object_id = ObjectId(category_id)

        # Find document by _id in the categories collection
        category = await db.categories.find_one({"_id": object_id})
        category_name = category.get("name", None) if category else None

        return category_name
    except Exception as e:
        print(f"Error finding category: {e}")
        traceback.print_exc()
        return None


