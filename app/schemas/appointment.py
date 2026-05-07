from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
    IN_PERSON = "in_person"
    TELECONSULTATION = "teleconsultation"


# Shared properties
class AppointmentBase(BaseModel):
    patient_id: int = Field(..., examples=[1])
    doctor_id: int = Field(..., examples=[1])
    hospital_id: Optional[int] = Field(None, examples=[1])
    start_time: datetime = Field(..., examples=["2024-05-01T10:00:00"])
    end_time: datetime = Field(..., examples=["2024-05-01T10:30:00"])
    status: AppointmentStatus = Field(AppointmentStatus.SCHEDULED, examples=["scheduled"])
    appointment_type: AppointmentType = Field(AppointmentType.IN_PERSON, examples=["in_person"])
    reason: Optional[str] = Field(None, examples=["Chest pain and breathlessness"])
    notes: Optional[str] = Field(None, examples=["Routine checkup"])


# Properties to receive on appointment creation
class AppointmentCreate(AppointmentBase):
    pass


# Properties to receive on appointment update
class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    appointment_type: Optional[AppointmentType] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


# Properties shared by models stored in DB
class AppointmentInDBBase(AppointmentBase):
    id: int
    token_number: Optional[int] = None
    cancellation_reason: Optional[str] = None
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
    hospital_name: Optional[str] = None
