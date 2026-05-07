"""
CRUD operations for Patients.
"""
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.crud.crud_base import CRUDBase
from app.models import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


class CRUDPatient(CRUDBase[Patient, PatientCreate, PatientUpdate]):
    """Patient CRUD operations."""

    def get_by_email(self, db: Session, *, email: str) -> Optional[Patient]:
        """Get patient by email."""
        return db.query(Patient).filter(Patient.email == email).first()

    def get_by_phone(self, db: Session, *, phone: str) -> Optional[Patient]:
        """Get patient by phone number."""
        return db.query(Patient).filter(Patient.phone == phone).first()

    def create(self, db: Session, *, obj_in: PatientCreate) -> Patient:
        """Create new patient."""
        db_obj = Patient(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Patient, obj_in: Union[PatientUpdate, Dict[str, Any]]) -> Patient:
        """Update patient."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def search(self, db: Session, *, query: str, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Search patients by name, email, or phone."""
        search_filter = or_(
            Patient.first_name.ilike(f"%{query}%"),
            Patient.last_name.ilike(f"%{query}%"),
            Patient.email.ilike(f"%{query}%"),
            Patient.phone.ilike(f"%{query}%"),
        )
        return db.query(Patient).filter(search_filter).offset(skip).limit(limit).all()

    def delete(self, db: Session, *, db_obj: Patient) -> Patient:
        """Delete patient."""
        db.delete(db_obj)
        db.commit()
        return db_obj

    def remove(self, db: Session, *, id: int) -> Patient:
        """Remove patient by ID."""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


patient = CRUDPatient(Patient)
