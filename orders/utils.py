import traceback
from db import db
from bson import ObjectId
from fastapi import status
from pymongo import UpdateOne



async def validate_ids_and_qty(item_id, item_info, items_data):
    try:
        item_data = items_data.get(item_id, None)
        # validate correct item_id
        if not item_data:
            return False, f"Item with id {item_id} not found", 0
        # print(item_data)

        total_amt = 0
        size_info = item_data.get("size_info", {})
        for size_id, qty in item_info.items():
            # validate correct size_id
            if size_id not in size_info:
                return False, f"Invalid size_id {size_id} for item {item_id}", 0

            # validate sufficient stock
            if size_info[size_id].get("available_qty", 0) < qty:
                return False, f"Insufficient stock for item {item_id}, size {size_id}", 0

            total_amt += size_info[size_id].get("price", 0) * qty

        return True, "All size_ids are valid and stock is sufficient", total_amt

    except Exception as e:
        traceback.print_exc()
        print("Error in validate_size_ids_and_qty:", e)
        return False, "Internal Server Error: " + str(e), 0



async def get_category_wise_items(item_id, item_info, items_data, category_data):
    try:
        item = items_data.get(item_id, {})
        if not item:
            return "", {}

        # print("Item found:", item)
        category_id = item.get("category", {}).get("category_id", None)
        category_id = str(category_id) if category_id else None
        category_name = category_data.get(category_id, "")
        print("category_id:", category_id)
        print("category_name:", category_name)

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


async def deduct_stock_for_order(items_with_qty):
    try:
        # Step 1: Fetch all items in one query for validation
        item_ids = [ObjectId(item_id) for item_id, _ in items_with_qty]
        items_cursor = db.items.find({"_id": {"$in": item_ids}})
        items_data = {str(item["_id"]): item async for item in items_cursor}

        print("items data", items_data)

        # input("Press Enter to continue...")  # Debugging pause

        # Step 2: Validate all items and sizes
        bulk_operations = []
        
        for item_id, item_info in items_with_qty:
            item_obj_id = ObjectId(item_id)
            
            # Check if item exists
            if item_id not in items_data:
                print(f"Item with id {item_id} not found while deducting stock")
                continue
            
            item_data = items_data[item_id]
            size_info = item_data.get("size_info", {})
            
            # Validate all sizes and check stock availability
            inc_operations = {}
            all_valid = True
            
            for size_id, qty in item_info.items():
                if size_id not in size_info:
                    print(f"Size id {size_id} not found in item {item_id} while deducting stock")
                    all_valid = False
                    continue
                
                available_qty = size_info[size_id].get("available_qty", 0)
                if available_qty < qty:
                    print(f"Insufficient stock for item {item_id}, size {size_id}. Available: {available_qty}, Required: {qty}")
                    all_valid = False
                    continue
                
                # Prepare the increment operation (negative value to deduct)
                inc_operations[f"size_info.{size_id}.available_qty"] = -qty
                print(f"Will deduct {qty} from item {item_id}, size {size_id}. Current: {available_qty}, New: {available_qty - qty}")

            # Only add to bulk operations if all validations passed
            if inc_operations:
                bulk_operations.append(
                    UpdateOne(
                        {"_id": item_obj_id},
                        {"$inc": inc_operations}
                    )
                )

        # with open("bulk_operations.txt", "w") as f:
        #     f.write(f"{bulk_operations}\n")

        # input("Press Enter to continue...")  # Debugging pause

        # Step 3: Execute all updates in one go
        if bulk_operations:
            result = await db.items.bulk_write(bulk_operations, ordered=False)
            print(f"✅ Bulk stock deduction completed: {result.modified_count} items updated")
            return {"message": f"Successfully deducted stock from {result.modified_count} items"}, status.HTTP_200_OK
        else:
            print("⚠️ No valid items to deduct stock from")
            return {"message": "No valid items found to deduct stock"}, status.HTTP_400_BAD_REQUEST

    except Exception as e:
        traceback.print_exc()
        print("Error in deduct_stock_per_order:", e)
        return {"message": f"Internal Server Error: {str(e)}"}, status.HTTP_500_INTERNAL_SERVER_ERROR


