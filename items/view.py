import traceback
from items.control import get_all_items
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Form, File, UploadFile, status




item_router = APIRouter(prefix="/items", tags=["items"])



@item_router.get("/")
def item_route_health():
    return JSONResponse(content={"message": "Item route is healthy"})


@item_router.get("/get_all_items")
def get_all_items_route():
    try:
        # TODO: update separate DB with count, like how many times this API is being called
        # TODO: add pagination
        response, status_code = get_all_items()
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while fetching items:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error", "items": []}
        )



