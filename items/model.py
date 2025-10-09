from typing import Dict
from pydantic import BaseModel, model_validator

class SizeInfo(BaseModel):
    size: str
    mrp: float
    price: float
    pieces: int
    available_qty: int

    @model_validator(mode='after')
    def check_mrp_greater_than_price(self):
        if self.mrp < self.price:
            raise ValueError('MRP must be greater than or equal to price')
        return self


class Item(BaseModel):
    name: str
    category_id: str
    company: str
    description: str
    size_info: Dict[str, SizeInfo]


class Category(BaseModel):
    name: str
    description: str

class ItemUpdate(BaseModel):
    item_id: str
    item_data: Item

