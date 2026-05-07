from app.models.base import Base
from app.models.user import User, UserRole
from app.models.address import Address
from app.models.hospital import Hospital, HospitalType, HospitalStatus, HospitalPatient
from app.models.department import Department
from app.models.patient import Patient
from app.models.doctor import Doctor, Availability
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.medical_record import MedicalRecord
from app.models.otp_request import OTPRequest

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Address",
    "Hospital",
    "HospitalType",
    "HospitalStatus",
    "Department",
    "Patient",
    "Doctor",
    "Availability",
    "Appointment",
    "AppointmentStatus",
    "AppointmentType",
    "MedicalRecord",
    "OTPRequest",
]
