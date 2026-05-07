from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, time


# Shared properties
class DoctorBase(BaseModel):
    first_name: str = Field(..., examples=["Priya"])
    last_name: str = Field(..., examples=["Sharma"])
    email: EmailStr = Field(..., examples=["priya.sharma@hospital.com"])
    phone: str = Field(..., examples=["+919876543210"])
    gender: Optional[str] = Field(None, examples=["female"])
    profile_image_url: Optional[str] = None
    specialization: str = Field(..., examples=["Cardiology"])
    qualification: Optional[str] = Field(None, examples=["MBBS, MD"])
    registration_number: Optional[str] = Field(None, examples=["MCI-12345"])
    experience_years: Optional[int] = Field(None, examples=[10])
    languages: Optional[str] = Field(None, examples=["Hindi,English,Kannada"])
    bio: Optional[str] = None
    fee: Optional[int] = Field(None, examples=[500])
    hospital_id: Optional[int] = None
    department_id: Optional[int] = None


# Properties to receive on doctor creation
class DoctorCreate(DoctorBase):
    pass


# Properties to receive on doctor update
class DoctorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    profile_image_url: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    registration_number: Optional[str] = None
    experience_years: Optional[int] = None
    languages: Optional[str] = None
    bio: Optional[str] = None
    fee: Optional[int] = None
    hospital_id: Optional[int] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


# Properties shared by models stored in DB
class DoctorInDBBase(DoctorBase):
    id: int
    address_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class Doctor(DoctorInDBBase):
    pass


# Properties stored in DB
class DoctorInDB(DoctorInDBBase):
    pass


# Availability schemas
class AvailabilityBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    is_available: bool = True


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityUpdate(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None


class AvailabilityInDBBase(AvailabilityBase):
    id: int
    doctor_id: int

    class Config:
        from_attributes = True


class Availability(AvailabilityInDBBase):
    pass


class DoctorWithAvailability(Doctor):
    availabilities: List[Availability] = []
