from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

# Shared properties
class AppointmentBase(BaseModel):
    patient_id: int = Field(..., examples=[1])
    doctor_id: int = Field(..., examples=[1])
    start_time: datetime = Field(..., examples=["2024-05-01T10:00:00"])
    end_time: datetime = Field(..., examples=["2024-05-01T11:00:00"])
    status: AppointmentStatus = Field(AppointmentStatus.SCHEDULED, examples=["scheduled"])
    notes: Optional[str] = Field(None, examples=["Routine checkup"])

# Properties to receive on appointment creation
class AppointmentCreate(AppointmentBase):
    pass

# Properties to receive on appointment update
class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

# Properties shared by models stored in DB
class AppointmentInDBBase(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Properties to return to client
class Appointment(AppointmentInDBBase):
    pass

# Properties stored in DB
class AppointmentInDB(AppointmentInDBBase):
    pass

# Appointment with patient and doctor details
class AppointmentDetail(Appointment):
    patient_name: str
    doctor_name: str
    doctor_specialization: str
