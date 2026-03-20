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


class ItemCreate(BaseModel):
    name: str
    unit_price: float | None = None


class ItemUpdate(BaseModel):
    name: str
    unit_price: float | None = None


class ItemResponse(BaseModel):
    id: int
    name: str
    unit_price: float | None
    vendor_id: int