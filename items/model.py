from pydantic import BaseModel

class Item(BaseModel):
    name: str
    category: str
    company: str
    size: str
    price: float
    pieces: int
    available_quantity: int
    description: str



class Category(BaseModel):
    name: str
    description: str
