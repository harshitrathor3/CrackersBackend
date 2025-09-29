import traceback
from db import db
from fastapi import status



async def get_all_items():
    try:
        res = []
        async for item in db.items.find({}):
            res.append(
                {
                    "_id": str(item.get("_id", None)),
                    "name": item.get("name", None),
                    "category": item.get("category", None),
                    "company": item.get("company", None),
                    "size": item.get("size", None),
                    "price": item.get("price", None),
                    "pieces": item.get("pieces", None),
                    "available_quantity": item.get("available_quantity", None),
                    "description": item.get("description", None)
                }
            )

        return {"items": res}, status.HTTP_200_OK

    except Exception as e:
        print("Error in get_all_items:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error","items": res}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def add_item(item_data):
    try:
        # Check if item with same name and company already exists
        existing_item = await db.items.find_one(
            {
                "name": item_data.get("name", None),
                "category": item_data.get("category", None),
                "company": item_data.get("company", None),
                "size": item_data.get("size", None),
                "price": item_data.get("price", None),
                "pieces": item_data.get("pieces", None),
            }
        )
        if existing_item:
            return {"message": "Item with same name and company already exists"}, status.HTTP_400_BAD_REQUEST

        # Insert new item
        await db.items.insert_one(item_data)
        return {"message": "Item added successfully"}, status.HTTP_201_CREATED

    except Exception as e:
        print("Error in add_item:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR
