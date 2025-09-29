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

