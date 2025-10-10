from typing import Dict
from typing import Optional
from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, model_validator



class Customer(BaseModel):
    first_name: str
    last_name: str
    mobile: Optional[str] = Field(
        None,
        pattern=r'^[1-9]\d{9}$',
        min_length=10,
        max_length=10,
        description="10-digit mobile number that cannot start with 0"
    )
    email: Optional[str] = Field(
        None,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description="Valid email address"
    )

    @model_validator(mode='after')
    def check_contact_info(self):
        if not self.mobile and not self.email:
            raise ValueError('Either mobile or email must be provided')
        return self


class Order(BaseModel):
    customer: Customer
    items: Dict[str, Dict[str, int]]  # key is item_id


class OrderItem(BaseModel):
    first_name: str
    last_name: str
    mobile: Optional[str] = Field(
        None,
        pattern=r'^[1-9]\d{9}$',
        min_length=10,
        max_length=10,
        description="10-digit mobile number that cannot start with 0"
    )
    email: Optional[str] = Field(
        None,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description="Valid email address"
    )
    items: Dict[str, Dict[str, int]]  # key is item_id
    total_amt: float
    total_discount: float
    status: str = "pending"
    # discount: float TODO think about it in future



