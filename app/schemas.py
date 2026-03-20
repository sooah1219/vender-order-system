from pydantic import BaseModel


class VendorCreate(BaseModel):
    name: str
    phone: str
    available_days: str


class VendorResponse(BaseModel):
    id: int
    name: str
    phone: str
    available_days: str