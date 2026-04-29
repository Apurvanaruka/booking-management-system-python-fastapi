from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime

# Shared properties
class PatientBase(BaseModel):
    first_name: str = Field(..., examples=["John"])
    last_name: str = Field(..., examples=["Doe"])
    date_of_birth: date = Field(..., examples=["1990-01-01"])
    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    phone: str = Field(..., examples=["+1234567890"])
    address: str = Field(..., examples=["123 Main St, Springfield"])
    insurance_provider: Optional[str] = Field(None, examples=["Blue Cross"])
    insurance_id: Optional[str] = Field(None, examples=["BC123456789"])

# Properties to receive on patient creation
class PatientCreate(PatientBase):
    pass

# Properties to receive on patient update
class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None

# Properties shared by models stored in DB
class PatientInDBBase(PatientBase):
    id: int
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

