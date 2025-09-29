import traceback
from items.model import Item
from fastapi.responses import JSONResponse
from items.control import add_item, get_all_items
from fastapi import APIRouter, Form, File, UploadFile, status




item_router = APIRouter(prefix="/items", tags=["items"])



@item_router.get("/")
async def item_route_health():
    return JSONResponse(content={"message": "Item route is healthy"})


@item_router.get("/get_all_items")
async def get_all_items_route():
    try:
        # TODO: update separate DB with count, like how many times this API is being called
        # TODO: add pagination
        response, status_code = await get_all_items()
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while fetching items:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error", "items": []}
        )

@item_router.post("/add_item")
async def add_item_route(item_data: Item):
    try:
        # TODO add authentication and authorization
        item_data = item_data.model_dump()
        print("Received item data:", item_data)

        response, status_code = await add_item(item_data)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error in add_item_route while parsing data:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid input data"}
        )

