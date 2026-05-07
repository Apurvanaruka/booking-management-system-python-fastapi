from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime


# Shared properties
class PatientBase(BaseModel):
    first_name: str = Field(..., examples=["Rahul"])
    last_name: str = Field(..., examples=["Kumar"])
    phone: str = Field(..., examples=["+919876543210"])
    date_of_birth: Optional[date] = Field(None, examples=["1990-01-01"])
    gender: Optional[str] = Field(None, examples=["male"])
    blood_group: Optional[str] = Field(None, examples=["B+"])
    email: Optional[EmailStr] = Field(None, examples=["rahul@example.com"])
    aadhaar_number: Optional[str] = Field(None, examples=["XXXX-XXXX-1234"])
    abha_id: Optional[str] = Field(None, examples=["12-3456-7890-1234"])
    emergency_contact_name: Optional[str] = Field(None, examples=["Sita Kumar"])
    emergency_contact_phone: Optional[str] = Field(None, examples=["+919876543211"])
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None


# Properties to receive on patient creation
class PatientCreate(PatientBase):
    pass


# Properties to receive on patient update
class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    aadhaar_number: Optional[str] = None
    abha_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None


# Properties shared by models stored in DB
class PatientInDBBase(PatientBase):
    id: int
    address_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class Patient(PatientInDBBase):
    pass


# Properties stored in DB
class PatientInDB(PatientInDBBase):
    pass
