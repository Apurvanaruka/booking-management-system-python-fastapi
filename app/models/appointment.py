import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(enum.Enum):
    IN_PERSON = "in_person"
    TELECONSULTATION = "teleconsultation"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(String, default=AppointmentStatus.SCHEDULED.value)
    appointment_type = Column(String, default=AppointmentType.IN_PERSON.value)
    reason = Column(Text, nullable=True)  # symptoms / reason for visit
    notes = Column(Text, nullable=True)
    token_number = Column(Integer, nullable=True)  # queue number
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    hospital = relationship("Hospital", back_populates="appointments")
    medical_records = relationship("MedicalRecord", back_populates="appointment")
