from typing import Dict
from pydantic import BaseModel

class SizeInfo(BaseModel):
    size: str
    price: float
    pieces: int
    available_qty: int


class Item(BaseModel):
    name: str
    category_id: str
    company: str
    description: str
    size_info: Dict[str, SizeInfo]


class Category(BaseModel):
    name: str
    description: str
