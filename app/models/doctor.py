from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Time, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=False)
    gender = Column(String, nullable=True)  # male, female, other
    profile_image_url = Column(String, nullable=True)

    # Professional info
    specialization = Column(String, nullable=False)
    qualification = Column(String, nullable=True)  # MBBS, MD, MS, etc.
    registration_number = Column(String, unique=True, nullable=True, index=True)  # MCI/NMC
    experience_years = Column(Integer, nullable=True)
    languages = Column(String, nullable=True)  # comma-separated: "Hindi,English,Tamil"
    bio = Column(Text, nullable=True)

    # Fee
    fee = Column(Integer, nullable=True)  # in INR

    # Hospital & Department linkage
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Address
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    hospital = relationship("Hospital", back_populates="doctors")
    department = relationship("Department", back_populates="doctors")
    address = relationship("Address", foreign_keys=[address_id])
    appointments = relationship("Appointment", back_populates="doctor")
    availabilities = relationship("Availability", back_populates="doctor")


class Availability(Base):
    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time = Column(Time)
    end_time = Column(Time)
    is_available = Column(Boolean, default=True)

    # Relationships
    doctor = relationship("Doctor", back_populates="availabilities")
