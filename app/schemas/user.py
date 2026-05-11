from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    STAFF = "staff"
    HOSPITAL = "hospital"
    RECEPTIONIST = "receptionist"



# Shared properties
class UserBase(BaseModel):
    username: str = Field(..., examples=["user123"])
    email: Optional[EmailStr] = Field(None, examples=["user@example.com"])
    is_active: bool = Field(True, examples=[True])
    role: UserRole = Field(..., examples=["patient"])
    phone_number: Optional[str] = Field(None, examples=["+919876543210"])


# Properties to receive on user creation
class UserCreate(UserBase):
    password: Optional[str] = None  # nullable for OTP-only users
    reference_id: Optional[int] = None


# Properties to receive on user update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    reference_id: Optional[int] = None
    phone_number: Optional[str] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class User(UserInDBBase):
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: Optional[str] = None


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    role: Optional[str] = None


# OTP schemas
class OTPSendRequest(BaseModel):
    phone_number: str = Field(..., examples=["+919876543210"])


class OTPSendResponse(BaseModel):
    message: str = "OTP sent successfully"
    phone_number: str
    expires_in_seconds: int = 300


class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(..., examples=["+919876543210"])
    otp: str = Field(..., min_length=6, max_length=6, examples=["123456"])


class OTPVerifyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False
