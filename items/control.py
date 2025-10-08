import uuid
import pytz
import traceback
from db import db
from bson import ObjectId
from fastapi import status
from datetime import datetime
from utility.image_utils import ImageUtils
from items.utils import find_category_by_id


async def get_all_items():
    try:
        res = []
        async for item in db.items.find({}):
            new_item_dict = {
                "_id": str(item.get("_id", None)),
                "name": item.get("name", None),
                "company": item.get("company", None),
                "description": item.get("description", None),
                "size_info": item.get("size_info", None),
                "category": dict(item.get("category", {})),
                "image_url": item.get("image_url", None),
            }
            new_item_dict["category"]["category_id"] = str(new_item_dict["category"].get("category_id", None))
            res.append(new_item_dict)

        return {"items": res}, status.HTTP_200_OK

    except Exception as e:
        print("Error in get_all_items:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error","items": res}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def add_item(item_data, image):
    try:
        # Upload image to cloudinary
        image_utils = ImageUtils(image)
        image_utils.save_image_locally()

        image_unique_name = f"{item_data.get('name', 'item')}_{uuid.uuid4().hex[:8]}"
        print("Generated image unique name:", image_unique_name)
        response, status_code = image_utils.upload_image(public_id=image_unique_name)

        print("Image upload response:", response)

        image_url = None
        if status_code == status.HTTP_201_CREATED:
            image_url = response.get("secure_url", None)
        item_data['image_url'] = image_url

        category_id = item_data.pop("category_id", None)
        category_name = await find_category_by_id(category_id)
        print("Category name:", category_name)

        if category_name is None or category_name == "":
            return {"message": "Invalid category ID"}, status.HTTP_400_BAD_REQUEST

        # Check if item with same name and company already exists - # TODO: improve this logic
        existing_item = await db.items.find_one(
            {
                "name": item_data.get("name", None),
                "company": item_data.get("company", None),
            }
        )
        if existing_item:
            return {"message": "Item with same name and company already exists"}, status.HTTP_400_BAD_REQUEST

        item_data['category'] = {
            "category_id": ObjectId(category_id),
            "category_name": category_name
        }

        print("Final item data to be inserted:", item_data)

        await db.items.insert_one(item_data)

        return {"message": "Item added successfully"}, status.HTTP_201_CREATED
    except Exception as e:
        print("Error in add_item:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        print("Cleaning up local image file...")
        image_utils.delete_local_saved_image()


async def get_all_categories():
    try:
        res = []
        async for category in db.categories.find({}):
            created_at = category.get("created_at", None)
            if created_at:
                # Convert UTC to IST for response
                ist = pytz.timezone('Asia/Kolkata')
                created_at = created_at.replace(tzinfo=pytz.UTC).astimezone(ist)

            res.append(
                {
                    "_id": str(category.get("_id", None)),
                    "name": category.get("name", None),
                    "created_at": created_at.isoformat() if created_at else None,
                    "description": category.get("description", None)
                }
            )
        
        print(res)
        return {"categories": res}, status.HTTP_200_OK
    except Exception as e:
        print("Error in get_all_categories:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error","categories": []}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def add_category(category_data):
    try:
        # Check if category with same name already exists
        existing_category = await db.categories.find_one(
            {
                "name": category_data.get("name", None),
            }
        )
        if existing_category:
            return {"message": "Category with same name already exists"}, status.HTTP_400_BAD_REQUEST

        # Insert new category
        # Add created_at timestamp in IST
        ist = pytz.timezone('Asia/Kolkata')
        category_data['created_at'] = datetime.now(ist)
        
        await db.categories.insert_one(category_data)
        return {"message": "Category added successfully"}, status.HTTP_201_CREATED

    except Exception as e:
        print("Error in add_category:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR


