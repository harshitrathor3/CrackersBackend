from fastapi.responses import JSONResponse
from fastapi import APIRouter, Form, File, UploadFile

from items.control import fun



item_router = APIRouter(prefix="/items", tags=["items"])



@item_router.get("/")
def item_route_health():
    return JSONResponse(content={"message": "Item route is healthy"})

