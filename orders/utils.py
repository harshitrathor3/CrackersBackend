import pytz
import httpx
import traceback
from db import db
from bson import ObjectId
from fastapi import status
from pymongo import UpdateOne
from config import BREVO_API_KEY, BREVO_URL, SENDER_EMAIL, SENDER_NAME, SUBJECT



async def validate_ids_and_qty(item_id, item_info, items_data):
    try:
        item_data = items_data.get(item_id, None)
        # validate correct item_id
        if not item_data:
            return False, f"Item with id {item_id} not found", 0
        # print(item_data)

        total_amt = 0
        total_discount = 0
        size_info = item_data.get("size_info", {})
        for size_id, qty in item_info.items():
            # validate correct size_id
            if size_id not in size_info:
                return False, f"Invalid size_id {size_id} for item {item_id}", 0

            # validate sufficient stock
            if size_info[size_id].get("available_qty", 0) < qty:
                return False, f"Insufficient stock for item {item_id}, size {size_id}", 0

            total_amt += size_info[size_id].get("price", 0) * qty
            total_discount += size_info[size_id].get("discount", 0) * size_info[size_id].get("mrp", 0) * qty / 100
        
        total_amt = round(total_amt, 2)
        total_discount = round(total_discount, 2)

        bulk_discount_qty = item_data.get("bulk_discount_qty", None)
        bulk_discount_percent = item_data.get("bulk_discount_percent", None)
        total_item_qty = sum(qty for qty in item_info.values())

        if bulk_discount_qty is not None and bulk_discount_percent is not None:
            if total_item_qty >= bulk_discount_qty:
                extra_discount = (total_amt * bulk_discount_percent) / 100
                total_amt -= extra_discount
                total_discount += extra_discount

        return True, "All size_ids are valid and stock is sufficient", total_amt, total_discount

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
            "size_info": size_info,
            "image_url": item.get("image_url", ""),
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



async def create_email_content(customer_name, order_id, items_with_qty, order_date, total_amount, total_discount):
    try:
        item_ids = [ObjectId(item_id) for item_id, _ in items_with_qty]
        items_cursor = db.items.find({"_id": {"$in": item_ids}})
        items_data = {str(item["_id"]): item async for item in items_cursor}

        items_html = ""
        for item_id, item_info in items_with_qty:
            item_data = items_data.get(item_id, None)
            if not item_data:
                continue

            item_name = item_data.get("name", "")
            company = item_data.get("company", "")
            size_info = item_data.get("size_info", {})

            for size_id, qty in item_info.items():
                size_data = size_info.get(size_id, {})
                size = size_data.get("size", "")
                pieces = size_data.get("pieces", 0)
                price = size_data.get("price", 0)
                mrp = size_data.get("mrp", 0)
                discount = size_data.get("discount", 0)
                subtotal = price * qty

                discount = round(discount * mrp * qty / 100, 2)

                items_html += f"""
<tr>
    <td style="padding: 8px; border-bottom: 1px solid #eee;">{item_name} - {size}</td>
    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">₹{mrp * qty}</td>
    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">₹{discount}</td>
    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">₹{subtotal}</td>
</tr>
"""


        email_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            margin: 0; 
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            width: 100%;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 6px;
            overflow: hidden;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
        }}
        .footer {{
            background-color: #f1f1f1;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        th, td {{
            padding: 8px;
            border-bottom: 1px solid #eee;
            font-size: 14px;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        td {{
            word-break: break-word;
        }}
        .total {{
            font-size: 16px;
            font-weight: bold;
            color: #4CAF50;
        }}
        @media only screen and (max-width: 480px) {{
            body, .container {{
                width: 100% !important;
                min-width: 100% !important;
            }}
            th, td {{
                font-size: 12px !important;
                padding: 6px !important;
            }}
            .total {{
                font-size: 14px !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Order Confirmed!</h1>
        </div>
        <div class="content">
            <p>प्रिय {customer_name},</p>

            <p>✨ <strong>जोशी फटाका</strong> से खरीदारी करने के लिए धन्यवाद! 🎆  
            हमें यह बताते हुए खुशी हो रही है कि आपका ऑर्डर सफलतापूर्वक तैयार कर दिया गया है और आपको सौंप दिया गया है।</p>

            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Order Id:</strong> {order_id}</p>
                <p style="margin: 5px 0;"><strong>Order date:</strong> {order_date.strftime("%d-%m-%Y")}</p>
                <p style="margin: 5px 0;"><strong>Order time:</strong> {order_date.strftime("%I:%M %p")}</p>
            </div>

            <h3 style="color: #4CAF50;">🧨 Your Order Summary:</h3>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align:left;">Item</th>
                            <th style="text-align:center;">Qty</th>
                            <th style="text-align:center;">Total Cost</th>
                            <th style="text-align:right;">Discount</th>
                            <th style="text-align:right;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
            </div>

            <div style="margin-top: 20px;">
                <table style="width: 100%; border-collapse: collapse; background-color: #f9f9f9; border-radius: 8px; padding: 10px;">
                    <tr style="border-top: 2px solid #ddd;">
                        <td style="padding: 10px; text-align: left; font-weight: bold; font-size: 16px; color: #333;">Total Amount:</td>
                        <td style="padding: 10px; text-align: right; font-weight: bold; font-size: 16px; color: #4CAF50;">₹{total_amount}</td>
                    </tr>
                    <tr style="border-top: 2px solid #ddd;">
                        <td style="padding: 10px; text-align: left; font-weight: bold; font-size: 16px; color: #333;">Amount Saved:</td>
                        <td style="padding: 10px; text-align: right; font-weight: bold; font-size: 16px; color: #4CAF50;">₹{total_discount}</td>
                    </tr>
                </table>
            </div>

            <p style="margin-top: 20px;">हमें आशा है कि आपको हमारी सेवा पसंद आई होगी! अगली बार भी <strong>जोशी फटाका</strong> पर ऑर्डर करें और पाएं शानदार छूट और तेज़ सेवा 🔥</p>
            <br>
            <p>आपको और आपके परिवार को दीपावली की हार्दिक शुभकामनाएँ! आपका जीवन रोशनी, खुशियों और उत्सवों से भर जाए 🎇</p>
        </div>
        <div class="footer">
            <p>स्नेह सहित,<br><strong>टीम जोशी फटाका 💥</strong></p>
            <p>This is an automated email. Please do not reply to this message.</p>
        </div>
    </div>
</body>
</html>
"""

        return email_content

    except Exception as e:
        print("Error in create_email_content:", e)
        traceback.print_exc()
        return "<h1>Order Confirmation</h1><p>Thank you for your order!</p>"



async def send_order_confirmation_email(order_details):
    try:
        # TODO add discount availed in email
        order_id = str(order_details.get("_id", "N/A"))
        customer_name = order_details.get("first_name", "Valued Customer")
        customer_email = order_details.get("email", None)
        total_amount = order_details.get("total_amt", 0)
        order_date = order_details.get("order_date", "")
        items_with_qty = order_details.get("items", {}).items()
        total_discount = order_details.get("total_discount", 0)
    
        if order_date:
            ist = pytz.timezone('Asia/Kolkata')
            order_date = order_date.replace(tzinfo=pytz.UTC).astimezone(ist)

        # build email content
        email_content = await create_email_content(customer_name, order_id, items_with_qty, order_date, total_amount, total_discount)
        # with open("email_content.html", "w") as f:
        #     f.write(email_content)

        # email_content = "<h1>Order Confirmation</h1>"

        # Send email via Brevo
        # TODO add few emails in CC
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
            BREVO_URL,
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
                "to": [{"email": customer_email, "name": customer_name}],
                "cc": [
                    {"email": "harshitrathorelink@gmail.com"},
                    {"email": "shobhitjoshi87@gmail.com"}
                ],
                "subject": SUBJECT,
                "htmlContent": email_content
            }
        )

            if response.status_code == 201:
                print(f"✅ Order confirmation email sent to {customer_email}")
                return True, status.HTTP_200_OK
            else:
                print(f"❌ Failed to send email: {response.status_code} - {response.text}")
                return False, status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as e:
        traceback.print_exc()
        print("Error sending confirmation email:", e)
        return False, status.HTTP_500_INTERNAL_SERVER_ERROR


