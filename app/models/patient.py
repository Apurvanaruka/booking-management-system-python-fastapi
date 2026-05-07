from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)  # male, female, other
    blood_group = Column(String, nullable=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    email = Column(String, unique=True, nullable=True, index=True)
    phone = Column(String, unique=True, nullable=False, index=True)

    # Address
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)

    # India-specific
    aadhaar_number = Column(String, nullable=True)
    abha_id = Column(String, nullable=True)  # Ayushman Bharat Health Account

    # Emergency contact
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)

    # Insurance (optional for India)
    insurance_provider = Column(String, nullable=True)
    insurance_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    address = relationship("Address", foreign_keys=[address_id])
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    hospital_patients = relationship("HospitalPatient", back_populates="patient")
