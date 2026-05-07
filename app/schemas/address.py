from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AddressBase(BaseModel):
    line1: str = Field(..., examples=["123, MG Road"])
    line2: Optional[str] = Field(None, examples=["Near City Mall"])
    landmark: Optional[str] = Field(None, examples=["Opposite SBI Bank"])
    city: str = Field(..., examples=["Bengaluru"])
    district: Optional[str] = Field(None, examples=["Bengaluru Urban"])
    state: str = Field(..., examples=["Karnataka"])
    pincode: str = Field(..., examples=["560001"])
    country: str = Field("India", examples=["India"])
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_type: Optional[str] = Field(None, examples=["hospital"])


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_type: Optional[str] = None


class AddressInDBBase(AddressBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Address(AddressInDBBase):
    pass
