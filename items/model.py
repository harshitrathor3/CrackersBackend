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
    bulk_discount_qty: int | None = None
    bulk_discount_percent: float | None = None

    @model_validator(mode='after')
    def check_bulk_discount_values(self):
        if self.bulk_discount_qty is not None and self.bulk_discount_qty <= 0:
            raise ValueError('bulk_discount_qty must be greater than 0')
        if self.bulk_discount_percent is not None and self.bulk_discount_percent <= 0:
            raise ValueError('bulk_discount_percent must be greater than 0')
        return self


class Category(BaseModel):
    name: str
    description: str

class ItemUpdate(BaseModel):
    item_id: str
    item_data: Item

