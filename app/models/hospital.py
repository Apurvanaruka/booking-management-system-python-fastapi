import enum
from datetime import time
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class HospitalType(enum.Enum):
    GOVERNMENT = "government"
    PRIVATE = "private"
    CLINIC = "clinic"
    NURSING_HOME = "nursing_home"
    DIAGNOSTIC_CENTER = "diagnostic_center"


class HospitalStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    booking_slug = Column(String, unique=True, nullable=False, index=True)  # e.g. "apollo-mumbai"
    registration_number = Column(String, unique=True, nullable=True, index=True)
    hospital_type = Column(String, default=HospitalType.PRIVATE.value)
    phone = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    website = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)

    # Address
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)

    # Verification / Admin approval
    status = Column(String, default=HospitalStatus.PENDING.value)
    verification_notes = Column(Text, nullable=True)

    # Global Scheduling Settings
    slot_duration_minutes = Column(Integer, default=30)
    working_hours_start = Column(Time, default=time(9, 0))
    working_hours_end = Column(Time, default=time(17, 0))
    lunch_break_start = Column(Time, nullable=True)
    lunch_break_end = Column(Time, nullable=True)
    working_days = Column(String, default="0,1,2,3,4,5")  # 0=Mon, 6=Sun

    # Owner (the user who registered this hospital)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    address = relationship("Address", foreign_keys=[address_id])
    owner = relationship("User", foreign_keys=[owner_user_id])
    doctors = relationship("Doctor", back_populates="hospital")
    departments = relationship("Department", back_populates="hospital")
    appointments = relationship("Appointment", back_populates="hospital")
    hospital_patients = relationship("HospitalPatient", back_populates="hospital")


class HospitalPatient(Base):
    """Junction table: tracks which patients are registered at which hospitals."""
    __tablename__ = "hospital_patients"
    __table_args__ = (UniqueConstraint('hospital_id', 'patient_id', name='uq_hospital_patient'),)

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    hospital = relationship("Hospital", back_populates="hospital_patients")
    patient = relationship("Patient", back_populates="hospital_patients")
