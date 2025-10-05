import traceback
from db import db
from bson import ObjectId



async def validate_ids_and_qty(item_obj_id, item_info):
    try:
        item_data = await db.items.find_one({"_id": item_obj_id})
        # validate correct item_id
        if not item_data:
            return False, f"Item with id {item_obj_id} not found", 0
        print(item_data)

        total_amt = 0
        size_info = item_data.get("size_info", {})
        for size_id, qty in item_info.items():
            # validate correct size_id
            if size_id not in size_info:
                return False, f"Invalid size_id {size_id} for item {item_obj_id}", 0

            # validate sufficient stock
            if size_info[size_id].get("available_qty", 0) < qty:
                return False, f"Insufficient stock for item {item_obj_id}, size {size_id}", 0

            total_amt += size_info[size_id].get("price", 0) * qty

        return True, "All size_ids are valid and stock is sufficient", total_amt

    except Exception as e:
        traceback.print_exc()
        print("Error in validate_size_ids_and_qty:", e)
        return False, "Internal Server Error: " + str(e), 0



async def get_category_wise_items(item_id, item_info):
    try:
        item = await db.items.find_one({"_id": ObjectId(item_id)})
        if not item:
            return "", {}
        
        print("Item found:", item)

        category_id = item.get("category", {}).get("category_id", "")
        print("category_id:", category_id)
        category_name = await db.categories.find_one({"_id": ObjectId(category_id)})
        print("category_name:", category_name)
        category_name = category_name.get("name", "")

        item_name = item.get("name", "")
        company = item.get("company", "")
        description = item.get("description", "")
        size_info_all = item.get("size_info", {})
        size_info = {}

        for size_id, qty in item_info.items():
            size_data = size_info_all.get(size_id, {})
            if size_data:
                size_info[size_id] = {
                    "size": size_data.get("size", ""),
                    "price": size_data.get("price", 0),
                    "pieces": size_data.get("pieces", 0),
                    "qty": qty
                }

        order_item = {
            "item_name": item_name,
            "company": company,
            "description": description,
            "size_info": size_info
        }

        return category_name, order_item

    except Exception as e:
        traceback.print_exc()
        print("Error in get_category_wise_items:", e)
        return "", {}


