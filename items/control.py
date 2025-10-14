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
        categories = {str(cat["_id"]): cat["name"] async for cat in db.categories.find({})}

        item_cnt = 0
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
            new_item_dict["category"]["category_name"] = categories.get(new_item_dict["category"]["category_id"], "Other")
            res.append(new_item_dict)
            item_cnt += 1

        return {"items": res, "item_count": item_cnt}, status.HTTP_200_OK

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
        if not category_id or not ObjectId.is_valid(category_id):
            return {"message": "Invalid or missing category_id"}, status.HTTP_400_BAD_REQUEST

        existing_item = await db.items.find_one(
            {
                "name": item_data.get("name", None),
                "company": item_data.get("company", None),
            }
        )
        if existing_item:
            return {"message": "Item with same name and company already exists"}, status.HTTP_400_BAD_REQUEST

        # calculate discount
        size_info = item_data.get("size_info", {})
        for size_id, size_data in size_info.items():
            mrp = size_data.get("mrp", 0)
            price = size_data.get("price", 0)
            if mrp > 0:
                discount = round(((mrp - price) / mrp) * 100, 2)
            else:
                discount = 0.0
            size_data['discount'] = discount
            size_info[size_id] = size_data

        item_data['size_info'] = size_info
        item_data['category'] = {
            "category_id": ObjectId(category_id),
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

        category_cnt = 0
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
            category_cnt += 1
        
        print(res)
        return {"categories": res, "category_count": category_cnt}, status.HTTP_200_OK
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



async def get_all_item_category_wise():
    try:
        # fetch all categories
        categories = {str(cat["_id"]): cat["name"] async for cat in db.categories.find({})}
        print("categories:", categories)

        item_cnt = 0
        res = {"other": []}
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

            category_id = str(item.get("category", {}).get("category_id", ""))
            category_name = categories.get(category_id, "other")
            if category_name not in res:
                res[category_name] = []
            new_item_dict["category"]["category_id"] = category_id
            res[category_name].append(new_item_dict)
            item_cnt += 1
        
        category_cnt = len(res)

        return {"category_count": category_cnt, "item_count": item_cnt, "items": res,}, status.HTTP_200_OK

    except Exception as e:
        print("Error in get_all_items:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error", "items": res}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def update_item_details(item_id, update_data):
    try:
        if not ObjectId.is_valid(item_id):
            return {"message": "Invalid item_id"}, status.HTTP_400_BAD_REQUEST

        existing_item = await db.items.find_one({"_id": ObjectId(item_id)})
        if not existing_item:
            return {"message": "Item not found"}, status.HTTP_404_NOT_FOUND

        if "category_id" in update_data:
            category_id = update_data.pop("category_id")
            category = await find_category_by_id(category_id)
            if not category:
                return {"message": "Category not found"}, status.HTTP_404_NOT_FOUND
            update_data["category"] = {"category_id": ObjectId(category_id)}

        if "size_info" in update_data:
            size_info = update_data["size_info"]
            for size_id, size_data in size_info.items():
                mrp = size_data.get("mrp", 0)
                price = size_data.get("price", 0)
                if mrp > 0:
                    discount = round(((mrp - price) / mrp) * 100, 2)
                else:
                    discount = 0.0
                size_data['discount'] = discount
                size_info[size_id] = size_data
            update_data["size_info"] = size_info

        update_result = await db.items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )
        if update_result.modified_count == 1:
            return {"message": "Item updated successfully"}, status.HTTP_200_OK
        else:
            return {"message": "No changes made to the item"}, status.HTTP_200_OK

    except Exception as e:
        print("Error in update_item_details:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def delete_item(item_id):
    try:
        if not ObjectId.is_valid(item_id):
            return {"message": "Invalid item_id"}, status.HTTP_400_BAD_REQUEST

        existing_item = await db.items.find_one({"_id": ObjectId(item_id)})
        if not existing_item:
            return {"message": "Item not found"}, status.HTTP_404_NOT_FOUND

        delete_result = await db.items.delete_one({"_id": ObjectId(item_id)})
        if delete_result.deleted_count == 1:
            return {"message": "Item deleted successfully"}, status.HTTP_200_OK
        else:
            return {"message": "Failed to delete item"}, status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as e:
        print("Error in delete_item:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def search_items(query):
    try:
        if not query:
            return {"items": []}, status.HTTP_200_OK

        item_cnt = 0
        query = query.lower()
        res = []
        async for item in db.items.find(
            {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"company": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                ]
            }
        ):
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
            item_cnt += 1

        return {"items": res, "item_count": item_cnt}, status.HTTP_200_OK

    except Exception as e:
        print("Error in search_items:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error","items": []}, status.HTTP_500_INTERNAL_SERVER_ERROR



async def get_item_by_category_id(category_id):
    try:
        if not ObjectId.is_valid(category_id):
            return {"message": "Invalid category_id"}, status.HTTP_400_BAD_REQUEST
        
        category_name = await find_category_by_id(category_id)
        if not category_name:
            return {"message": "Category not found"}, status.HTTP_404_NOT_FOUND

        res = []
        item_cnt = 0
        async for item in db.items.find({"category.category_id": ObjectId(category_id)}):
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
            item_cnt += 1

        return {"category_name": category_name, "item_count": item_cnt, "items": res,}, status.HTTP_200_OK

    except Exception as e:
        print("Error in get_item_by_category_id:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error","items": []}, status.HTTP_500_INTERNAL_SERVER_ERROR


