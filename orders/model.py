from typing import Dict
from pydantic import BaseModel, Field



class Customer(BaseModel):
    first_name: str
    last_name: str
    mobile: str = Field(
        ...,
        pattern=r'^[1-9]\d{9}$',
        min_length=10,
        max_length=10,
        description="10-digit mobile number that cannot start with 0"
    )


class Order(BaseModel):
    customer: Customer
    items: Dict[str, Dict[str, int]]  # key is item_id


class OrderItem(BaseModel):
    first_name: str
    last_name: str
    mobile: str = Field(
        ...,
        pattern=r'^[1-9]\d{9}$',
        min_length=10,
        max_length=10,
        description="10-digit mobile number that cannot start with 0"
    )
    items: Dict[str, Dict[str, int]]  # key is item_id
    total_amt: float
    status: str = "pending"
    # discount: float TODO think about it in future



