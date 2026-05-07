from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import datetime
from enum import Enum

from app.schemas.address import Address, AddressCreate


class HospitalType(str, Enum):
    GOVERNMENT = "government"
    PRIVATE = "private"
    CLINIC = "clinic"
    NURSING_HOME = "nursing_home"
    DIAGNOSTIC_CENTER = "diagnostic_center"


class HospitalStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class HospitalBase(BaseModel):
    name: str = Field(..., examples=["Apollo Hospitals"])
    registration_number: Optional[str] = Field(None, examples=["MH-12345"])
    hospital_type: HospitalType = Field(HospitalType.PRIVATE, examples=["private"])
    phone: str = Field(..., examples=["+919876543210"])
    email: EmailStr = Field(..., examples=["admin@apollo.com"])
    website: Optional[str] = Field(None, examples=["https://apollohospitals.com"])
    description: Optional[str] = Field(None, examples=["Multi-specialty hospital"])
    logo_url: Optional[str] = None
    
    # Scheduling settings
    slot_duration_minutes: int = Field(30, examples=[30])
    working_hours_start: datetime.time = Field(datetime.time(9, 0), examples=["09:00:00"])
    working_hours_end: datetime.time = Field(datetime.time(17, 0), examples=["17:00:00"])
    lunch_break_start: Optional[datetime.time] = Field(None, examples=["13:00:00"])
    lunch_break_end: Optional[datetime.time] = Field(None, examples=["14:00:00"])
    working_days: str = Field("0,1,2,3,4,5", examples=["0,1,2,3,4,5"])


class HospitalCreate(HospitalBase):
    address: Optional[AddressCreate] = None


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    hospital_type: Optional[HospitalType] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None

    slot_duration_minutes: Optional[int] = None
    working_hours_start: Optional[datetime.time] = None
    working_hours_end: Optional[datetime.time] = None
    lunch_break_start: Optional[datetime.time] = None
    lunch_break_end: Optional[datetime.time] = None
    working_days: Optional[str] = None


class HospitalInDBBase(HospitalBase):
    id: int
    booking_slug: str
    address_id: Optional[int] = None
    status: HospitalStatus = HospitalStatus.PENDING
    verification_notes: Optional[str] = None
    owner_user_id: int
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class Hospital(HospitalInDBBase):
    pass


class HospitalWithAddress(Hospital):
    address: Optional[Address] = None


class HospitalVerify(BaseModel):
    status: HospitalStatus = Field(..., examples=["verified"])
    verification_notes: Optional[str] = Field(None, examples=["Documents verified"])


# Registration schema — combines hospital + admin user creation
class HospitalRegistration(BaseModel):
    # Hospital info
    hospital_name: str = Field(..., examples=["Apollo Hospitals"])
    hospital_type: HospitalType = Field(HospitalType.PRIVATE, examples=["private"])
    registration_number: Optional[str] = Field(None, examples=["MH-12345"])
    hospital_phone: str = Field(..., examples=["+919876543210"])
    hospital_email: EmailStr = Field(..., examples=["admin@apollo.com"])
    description: Optional[str] = None

    # Address
    address: Optional[AddressCreate] = None

    # Admin user info
    admin_username: str = Field(..., examples=["apollo_admin"])
    admin_email: EmailStr = Field(..., examples=["admin@apollo.com"])
    admin_password: str = Field(..., examples=["securepassword123"])
    admin_phone: str = Field(..., examples=["+919876543210"])
