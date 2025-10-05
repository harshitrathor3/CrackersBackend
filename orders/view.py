import traceback
from orders.model import Order
from orders.control import place_order
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Form, File, UploadFile, status





orders_router = APIRouter(prefix="/orders", tags=["orders"])



@orders_router.get("/")
async def orders_route_health():
    return JSONResponse(content={"message": "Orders route is healthy"})


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


