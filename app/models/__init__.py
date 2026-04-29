from app.models.base import Base
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor, Availability
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_record import MedicalRecord

# Expose everything required when doing `from app.models import *`
__all__ = [
    "Base",
    "User",
    "UserRole",
    "Patient",
    "Doctor",
    "Availability",
    "Appointment",
    "AppointmentStatus",
    "MedicalRecord"
]
