import traceback
from orders.model import Order
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Form, File, UploadFile, status
from orders.control import get_orders, place_order, get_items_for_order





orders_router = APIRouter(prefix="/orders", tags=["orders"])



@orders_router.get("/")
async def orders_route_health():
    return JSONResponse(content={"message": "Orders route is healthy"})


@orders_router.get("/get_orders")
async def get_orders_route():
    try:
        response, status_code = await get_orders()
        return JSONResponse(content=response, status_code=status_code)
    except Exception as e:
        print("Error occurred while fetching orders:", e)
        traceback.print_exc()
        return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@orders_router.post("/place_order")
async def place_order_route(order_data: Order):
    try:
        order_data = order_data.model_dump()
        print("Received order data:", order_data)

        response, status_code = await place_order(order_data)
        return JSONResponse(content=response, status_code=status_code)
    except Exception as e:
        print("Error occurred while placing order:", e)
        traceback.print_exc()
        return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@orders_router.get("/get_items_for_order")
async def get_items_for_order_route(order_id: str):
    try:
        print("Fetching items for order_id:", order_id)
        response, status_code = await get_items_for_order(order_id)
        return JSONResponse(content=response, status_code=status_code)
    except Exception as e:
        print("Error occurred while fetching items:", e)
        traceback.print_exc()
        return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


