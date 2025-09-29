import traceback
from db import db
from fastapi import status


ans = db.items.find({})
print("ans", list(ans))





def get_all_items():
    try:
        res = []
        for item in db.items.find({}):
            res.append(
                {
                    "_id": str(item.get("_id", None)),
                    "name": item.get("name", None),
                    "category": item.get("category", None),
                    "company": item.get("company", None),
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


