import pytz
import traceback
from db import db
from urllib import parse
from bson import ObjectId
from fastapi import status
from datetime import datetime
from orders.model import OrderItem
from config import price_discount_values
from orders.utils import validate_ids_and_qty, get_category_wise_items, deduct_stock_for_order, send_order_confirmation_email




async def get_orders():
    try:
        orders = {"placed": [], "confirmed": [],}
        placed_cnt = 0
        confirmed_cnt = 0
        others_cnt = 0

        async for order in db.orders.find({}).sort("order_date", -1):
            order_date = order.get("order_date", None)
            order_confirmed_date = order.get("order_confirmed_date", None)
            if order_date:
                ist = pytz.timezone('Asia/Kolkata')
                order_date = order_date.replace(tzinfo=pytz.UTC).astimezone(ist)
            if order_confirmed_date:
                ist = pytz.timezone('Asia/Kolkata')
                order_confirmed_date = order_confirmed_date.replace(tzinfo=pytz.UTC).astimezone(ist)

            order_status = order.get("status", "placed")
            orders[order_status].append(
                {
                    "order_id": str(order["_id"]),
                    "first_name": order.get("first_name", ""),
                    "last_name": order.get("last_name", ""),
                    "mobile": order.get("mobile", ""),
                    "total_amt": order.get("total_amt", 0),
                    "status": order_status,
                    "order_date": order_date.isoformat() if order_date else None,
                    "order_confirmed_date": order_confirmed_date.isoformat() if order_confirmed_date else "",
                }
            )
            if order_status == "placed":
                placed_cnt += 1
            elif order_status == "confirmed":
                confirmed_cnt += 1
            else:
                others_cnt += 1

        orders["confirmed"].sort(key=lambda x: x.get("order_confirmed_date", ""), reverse=True)

        return {
            "total_orders": placed_cnt + confirmed_cnt + others_cnt,
            "orders": orders,
            "placed_count": placed_cnt,
            "confirmed_count": confirmed_cnt,
            "others_count": others_cnt,
        }, status.HTTP_200_OK

    except Exception as e:
        print("Error occurred while fetching orders:", e)
        traceback.print_exc()
        return {"message": str(e), "orders": orders}, status.HTTP_500_INTERNAL_SERVER_ERROR



async def place_order(order_data):
    try:
        # check correct size_ids
        # check sufficient stock

        customer_first_name = order_data.get("customer", {}).get("first_name", "")
        customer_last_name = order_data.get("customer", {}).get("last_name", "")
        customer_mobile = order_data.get("customer", {}).get("mobile", None)
        customer_email = order_data.get("customer", {}).get("email", None)

        # remove orders with 0 qty
        order_data["items"] = {item_id: {size_id: qty for size_id, qty in size_info.items() if qty > 0} for item_id, size_info in order_data.get("items", {}).items() if any(qty > 0 for qty in size_info.values())}
        print("Order data after removing 0 qty items:", order_data)
        # input("check order data after removing 0 qty items?")

        items = order_data.get("items", {}).items()

        items_data = {str(item["_id"]): item async for item in db.items.find({"_id": {"$in": [ObjectId(item_id) for item_id, _ in items]}})}
        # print("Items data fetched for order placement:", items_data)

        total_order_amt = 0
        total_discount_amt = 0
        for item_id, item_info in items:
            # validate size_ids and available quantity
            is_valid, message, total_amt, total_discount = await validate_ids_and_qty(item_id, item_info, items_data)
            if not is_valid:
                return {"message": message}, status.HTTP_400_BAD_REQUEST
            else:
                print(f"Item {item_id} passed validation: {message}")

            total_order_amt += total_amt
            total_discount_amt += total_discount

        # calculate final price after cart value discount
        special_discount = 0
        for price_threshold, discount_percent in sorted(price_discount_values.items(), reverse=True):
            if total_order_amt >= price_threshold:
                special_discount = (total_order_amt * discount_percent) / 100
                total_order_amt -= special_discount
                total_discount_amt += special_discount
                print(f"Applied cart value discount: {discount_percent}% for amount {total_order_amt + special_discount}")
                break

        # insert order into collection
        order_item = OrderItem(
            first_name=customer_first_name,
            last_name=customer_last_name,
            mobile=customer_mobile,
            email=customer_email,
            items=order_data.get("items", {}),
            total_amt=total_order_amt,
            total_discount=total_discount_amt,
            status="placed"
        )
        order_item = order_item.model_dump()
        order_item["order_date"] = datetime.now(pytz.timezone("Asia/Kolkata"))
        print("Inserting order:", order_item)
        order = await db.orders.insert_one(order_item)

        return {
            "order_id": str(order.inserted_id),
            "message": "Order placed successfully"
        }, status.HTTP_201_CREATED

    except Exception as e:
        print("Error occurred while placing order:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def get_items_for_order(order_id):
    try:
        if not ObjectId.is_valid(order_id):
            return {"message": "Invalid order_id"}, status.HTTP_400_BAD_REQUEST

        order_obj_id = ObjectId(order_id)
        order = await db.orders.find_one({"_id": order_obj_id})
        if not order:
            return {"message": "Order not found"}, status.HTTP_404_NOT_FOUND

        first_name = order.get("first_name", "")
        last_name = order.get("last_name", "")
        mobile = order.get("mobile", "")
        order_date = order.get("order_date", None)
        order_status = order.get("status", "")
        total_amt = order.get("total_amt", 0)
        items = order.get("items", {})

        if order_date:
            ist = pytz.timezone('Asia/Kolkata')
            order_date = order_date.replace(tzinfo=pytz.UTC).astimezone(ist)
            order_date = order_date.isoformat()

        # fetch all items
        items_data = {str(item["_id"]): item async for item in db.items.find({"_id": {"$in": [ObjectId(item_id) for item_id in items.keys()]}})}

        category_ids = set()
        for item in items_data.values():
            category_id = item.get("category", {}).get("category_id", None)

            if ObjectId.is_valid(category_id):
                category_ids.add(ObjectId(category_id))

        category_data = {str(category["_id"]): category.get("name", "") async for category in db.categories.find({"_id": {"$in": list(category_ids)}})}

        # print("Items data fetched for order:", items_data)
        print("category ids fetched for order:", category_ids)
        print("category wise items fetched for order:", category_data)

        # input("check items data fetched?")

        category_wise_items = {}
        for item_id, item_info in items.items():
            category, order_item = await get_category_wise_items(item_id, item_info, items_data, category_data)
            items_list = category_wise_items.get(category, [])
            items_list.append(order_item)
            category_wise_items[category] = items_list

        result = {
            "order_id": order_id,
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "order_date": order_date,
            "order_status": order_status,
            "total_amt": total_amt,
            "category_wise_items": category_wise_items,
        }

        return result, status.HTTP_200_OK


    except Exception as e:
        print("Error occurred while fetching items for order:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def confirm_order(order_id):
    try:
        if not ObjectId.is_valid(order_id):
            return {"message": "Invalid order_id"}, status.HTTP_400_BAD_REQUEST
        order_obj_id = ObjectId(order_id)

        # Check if order exists
        order = await db.orders.find_one({"_id": order_obj_id})
        if not order:
            return {"message": "Order not found"}, status.HTTP_404_NOT_FOUND

        items_with_qty = order.get("items", {}).items()
        print("Items with qty to deduct stock:", items_with_qty)

        order_status = order.get("status", "")

        # check order status
        if order_status not in ["placed", "confirmed"]:
            return {"message": "Order is not in 'placed' or 'confirmed' status"}, status.HTTP_400_BAD_REQUEST

        if order_status == "placed":
            # deduct stock from inventory
            await deduct_stock_for_order(items_with_qty)

        # send email to customer
        customer_email = order.get("email", "harshitrathorelink@gmail.com")
        email_sent_status = False
        if customer_email:
            print("Send order confirmation email to customer:", customer_email)
            res, status_code = await send_order_confirmation_email(order)

            if status_code == status.HTTP_200_OK:
                print("Order confirmation email sent successfully to", customer_email)
                email_sent_status = True

        # Update order status to 'confirmed'
        result = await db.orders.update_one(
            {"_id": order_obj_id},
            {
                "$set": {
                    "status": "confirmed",
                    "email_sent": email_sent_status,
                    "order_confirmed_date": datetime.now(pytz.timezone("Asia/Kolkata")),
                }
            }
        )

        whatsapp_msg = f"""
🎉 नमस्ते! आपने Joshi Fataka से खरीदारी की है 🧨  
आपका ऑर्डर सफलतापूर्वक कन्फर्म हो गया है।  

🧾 आपका ऑर्डर ID: {order_id}  
कृपया इसे भविष्य के संदर्भ के लिए संभाल कर रखें।  

हमारे साथ खरीदारी करने के लिए धन्यवाद!  
फिर मिलेंगे — शुभ दीपावली! 🪔🙏
"""
        encoded_msg = parse.quote(whatsapp_msg)

        if result.modified_count == 1:
            return {
                "message": "Order confirmed successfully",
                "whatsapp_msg_link": f"https://wa.me/91{order.get('mobile', '9926546160')}?text={encoded_msg}",
                "email_sent": email_sent_status,
            }, status.HTTP_200_OK
        else:
            return {
                "message": "Order status was already 'confirmed'",
                "whatsapp_msg_link": f"https://wa.me/91{order.get('mobile', '9926546160')}?text={encoded_msg}",
                "email_sent": email_sent_status,
            }, status.HTTP_200_OK

    except Exception as e:
        print("Error occurred while confirming order:", e)
        traceback.print_exc()
        return {"message": "Internal Server Error"}, status.HTTP_500_INTERNAL_SERVER_ERROR


