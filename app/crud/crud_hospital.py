from typing import Optional, List
import re
from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models import Hospital, HospitalPatient, Patient
from app.schemas.hospital import HospitalCreate, HospitalUpdate


class CRUDHospital(CRUDBase[Hospital, HospitalCreate, HospitalUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Hospital]:
        return db.query(Hospital).filter(Hospital.email == email).first()

    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Hospital]:
        return db.query(Hospital).filter(Hospital.booking_slug == slug).first()

    def get_by_registration_number(self, db: Session, *, registration_number: str) -> Optional[Hospital]:
        return db.query(Hospital).filter(Hospital.registration_number == registration_number).first()

    def get_by_owner(self, db: Session, *, owner_user_id: int) -> List[Hospital]:
        return db.query(Hospital).filter(Hospital.owner_user_id == owner_user_id).all()

    def get_verified(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Hospital]:
        """Get only verified/approved hospitals."""
        return db.query(Hospital).filter(
            Hospital.status == "verified",
            Hospital.is_active == True
        ).offset(skip).limit(limit).all()

    def get_pending(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Hospital]:
        """Get hospitals pending admin approval."""
        return db.query(Hospital).filter(
            Hospital.status == "pending"
        ).offset(skip).limit(limit).all()

    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate a URL-friendly slug from hospital name."""
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug

    def _ensure_unique_slug(self, db: Session, base_slug: str) -> str:
        """Ensure slug is unique by appending a number if needed."""
        slug = base_slug
        counter = 1
        while db.query(Hospital).filter(Hospital.booking_slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def create_with_owner(self, db: Session, *, obj_in: HospitalCreate, owner_user_id: int, address_id: Optional[int] = None) -> Hospital:
        base_slug = self._generate_slug(obj_in.name)
        unique_slug = self._ensure_unique_slug(db, base_slug)

        db_obj = Hospital(
            name=obj_in.name,
            booking_slug=unique_slug,
            registration_number=obj_in.registration_number,
            hospital_type=obj_in.hospital_type.value if hasattr(obj_in.hospital_type, 'value') else obj_in.hospital_type,
            phone=obj_in.phone,
            email=obj_in.email,
            website=obj_in.website,
            description=obj_in.description,
            logo_url=obj_in.logo_url,
            slot_duration_minutes=obj_in.slot_duration_minutes,
            working_hours_start=obj_in.working_hours_start,
            working_hours_end=obj_in.working_hours_end,
            lunch_break_start=obj_in.lunch_break_start,
            lunch_break_end=obj_in.lunch_break_end,
            working_days=obj_in.working_days,
            address_id=address_id,
            owner_user_id=owner_user_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def verify(self, db: Session, *, id: int, status: str, notes: Optional[str] = None) -> Optional[Hospital]:
        hospital = self.get(db, id=id)
        if not hospital:
            return None
        hospital.status = status
        hospital.verification_notes = notes
        db.commit()
        db.refresh(hospital)
        return hospital

    def search_by_city(self, db: Session, *, city: str, skip: int = 0, limit: int = 100) -> List[Hospital]:
        """Search verified hospitals by city (via address)."""
        from app.models import Address
        return db.query(Hospital).join(
            Address, Hospital.address_id == Address.id
        ).filter(
            Address.city.ilike(f"%{city}%"),
            Hospital.status == "verified",
            Hospital.is_active == True
        ).offset(skip).limit(limit).all()

    # ─── Patient-Hospital Linking ─────────────────
    def link_patient(self, db: Session, *, hospital_id: int, patient_id: int) -> HospitalPatient:
        """Link a patient to a hospital. Idempotent."""
        existing = db.query(HospitalPatient).filter(
            HospitalPatient.hospital_id == hospital_id,
            HospitalPatient.patient_id == patient_id,
        ).first()
        if existing:
            return existing

        link = HospitalPatient(hospital_id=hospital_id, patient_id=patient_id)
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    def get_hospital_patients(self, db: Session, *, hospital_id: int) -> List[Patient]:
        """Get all patients registered at a hospital."""
        return db.query(Patient).join(
            HospitalPatient, Patient.id == HospitalPatient.patient_id
        ).filter(HospitalPatient.hospital_id == hospital_id).all()


hospital = CRUDHospital(Hospital)

