import pytz
import traceback
from db import db
from bson import ObjectId
from fastapi import status
from datetime import datetime
from orders.model import OrderItem
from orders.utils import validate_ids_and_qty




async def get_orders():
    try:
        orders = []
        async for order in db.orders.find({}):
            order_date = order.get("order_date", None)
            if order_date:
                ist = pytz.timezone('Asia/Kolkata')
                order_date = order_date.replace(tzinfo=pytz.UTC).astimezone(ist)
            orders.append(
                {
                    "order_id": str(order["_id"]),
                    "first_name": order.get("first_name", ""),
                    "last_name": order.get("last_name", ""),
                    "mobile": order.get("mobile", ""),
                    "total_amt": order.get("total_amt", 0),
                    "status": order.get("status", ""),
                    "order_date": order_date.isoformat() if order_date else None,
                }
            )

        return {
            "orders": orders,
            "total_orders": len(orders)
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
        customer_mobile = order_data.get("customer", {}).get("mobile", "")

        items = order_data.get("items", {}).items()

        total_order_amt = 0
        for item_id, item_info in items:
            # check item_id is valid ObjectId
            if not ObjectId.is_valid(item_id):
                return {"message": f"Invalid item_id: {item_id}"}, status.HTTP_400_BAD_REQUEST

            item_obj_id = ObjectId(item_id)
            
            # validate size_ids and available quantity
            is_valid, message, total_amt = await validate_ids_and_qty(item_obj_id, item_info)
            if not is_valid:
                return {"message": message}, status.HTTP_400_BAD_REQUEST
            else:
                print(f"Item {item_id} passed validation: {message}")

            total_order_amt += total_amt

        # insert order into collection
        order_item = OrderItem(
            first_name=customer_first_name,
            last_name=customer_last_name,
            mobile=customer_mobile,
            items=order_data.get("items", {}),
            total_amt=total_order_amt,
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


