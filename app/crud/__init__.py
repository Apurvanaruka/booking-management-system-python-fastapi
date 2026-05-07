"""
CRUD package.
"""
from .crud_base import CRUDBase
from .crud_patient import patient
from .crud_doctor import doctor
from .crud_user import user
from .crud_hospital import hospital
from .crud_department import department
from .crud_address import address

__all__ = [
    "CRUDBase",
    "patient",
    "doctor",
    "user",
    "hospital",
    "department",
    "address",
]
