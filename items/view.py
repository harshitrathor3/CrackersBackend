import json
import traceback
from utility.image_utils import ImageUtils
from fastapi.responses import JSONResponse
from items.model import Item, Category, ItemUpdate
from fastapi import APIRouter, Form, File, UploadFile, status
from items.control import (
    add_item, get_all_items,
    get_all_categories, 
    add_category,
    get_all_item_category_wise, 
    update_item_details,
    delete_item,
    search_items,
    get_item_by_category_id,
    get_item_by_id,
)



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
async def add_item_route(
    name: str = Form(...),
    category_id: str = Form(...),
    company: str = Form(...),
    description: str = Form(...),
    size_info: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        # TODO add authentication and authorization
        item_data = {
            "name": name,
            "category_id": category_id,
            "company": company,
            "description": description,
            "size_info": dict(json.loads(size_info))
        }

        item_data = Item(**item_data).model_dump()
        print("Received item data:", item_data)

        response, status_code = await add_item(item_data, image)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error in add_item_route while parsing data:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid input data" + str(e)}
        )


@item_router.get("/get_all_categories")
async def get_all_categories_route():
    try:
        response, status_code = await get_all_categories()
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while fetching categories:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error", "categories": []}
        )


@item_router.post("/add_category")
async def add_category_route(
    name: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        category_data = {
            "name": name,
            "description": description,
        }
        category_data = Category(**category_data).model_dump()
        print("Received category data:", category_data)

        response, status_code = await add_category(category_data, image)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while adding category:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error"}
        )




@item_router.post("/test_image")
def test_image_route(image: UploadFile = File(...)):

    image_utils = ImageUtils(image)
    image_utils.save_image_locally()

    upload_result, status = image_utils.upload_image(public_id="my_img_uniqq")

    image_utils.delete_local_saved_image()

    print("Upload result:", upload_result)
    print("Status code:", status)

    return JSONResponse(content={"message": "Image route is healthy"})


@item_router.get("/get_all_items_category_wise")
async def get_all_items_category_wise_route():
    try:
        response, status_code = await get_all_item_category_wise()
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while fetching items:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error", "items": []}
        )


@item_router.post("/update_item_details")
async def update_item_details_route(update_item_data: ItemUpdate):
    try:
        item_id = update_item_data.item_id
        item_data = update_item_data.item_data.model_dump()
        print("Received item data for update:", item_id, item_data)

        response, status_code = await update_item_details(item_id, item_data)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while updating item details:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error"}
        )


@item_router.delete("/delete_item/{item_id}")
async def delete_item_route(item_id: str):
    try:
        response, status_code = await delete_item(item_id)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while deleting item:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error"}
        )


@item_router.get("/search_items")
async def search_items_route(query: str):
    try:
        print("query:", query)
        response, status_code = await search_items(query)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while searching items:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error", "items": []}
        )


@item_router.get("/get_item_by_category_id")
async def get_item_by_category_id_route(category_id: str):
    try:
        response, status_code = await get_item_by_category_id(category_id)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while fetching items by category_id:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error", "items": []}
        )


@item_router.get("/get_item_by_id")
async def get_item_by_id_route(item_id: str):
    try:
        response, status_code = await get_item_by_id(item_id)
        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        print("Error occurred while fetching item by item_id:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal Server Error", "items": []}
        )

