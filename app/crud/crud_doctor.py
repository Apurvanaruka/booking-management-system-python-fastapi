from typing import List, Optional, Dict, Any
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session, joinedload


from app.crud.crud_base import CRUDBase
from app.models import Doctor, Availability, Appointment
from app.schemas.doctor import DoctorCreate, DoctorUpdate, AvailabilityCreate

class CRUDDoctor(CRUDBase[Doctor, DoctorCreate, DoctorUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Doctor]:
        return db.query(Doctor).filter(Doctor.email == email).first()

    def get_by_specialization(self, db: Session, *, specialization: str) -> List[Doctor]:
        return db.query(Doctor).filter(Doctor.specialization == specialization).all()

    def get_with_availability(self, db: Session, *, id: int) -> Optional[Doctor]:
        return db.query(Doctor).options(joinedload(Doctor.availabilities)).filter(Doctor.id == id).first()

    def add_availability(self, db: Session, *, doctor_id: int, availability: AvailabilityCreate) -> Doctor:
        db_availability = Availability(
            doctor_id=doctor_id,
            day_of_week=availability.day_of_week,
            start_time=availability.start_time,
            end_time=availability.end_time,
            is_available=availability.is_available
        )
        db.add(db_availability)
        db.commit()

        return self.get_with_availability(db, id=doctor_id)

    def check_availability(self, db: Session, *, doctor_id: int, start_time: datetime, end_time: datetime) -> bool:
        day_of_week = start_time.weekday()

        availability = db.query(Availability).filter(
            Availability.doctor_id == doctor_id,
            Availability.day_of_week == day_of_week,
            Availability.is_available == True,
            Availability.start_time <= start_time.time(),
            Availability.end_time >= end_time.time()
        ).first()

        return availability is not None

    def get_available_slots(self, db: Session, *, doctor_id: int, date: datetime) -> List[Dict[str, Any]]:
        day_of_week = date.weekday()

        availabilities = db.query(Availability).filter(
            Availability.doctor_id == doctor_id,
            Availability.day_of_week == day_of_week,
            Availability.is_available == True
        ).all()

        if not availabilities:
            return []

        start_of_day = datetime.combine(date.date(), time.min)
        end_of_day = datetime.combine(date.date(), time.max)

        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time >= start_of_day,
            Appointment.end_time <= end_of_day,
            Appointment.status != "cancelled"
        ).all()

        slots = []
        for availability in availabilities:
            current_time = datetime.combine(date.date(), availability.start_time)
            end_time = datetime.combine(date.date(), availability.end_time)

            while current_time + timedelta(minutes=30) <= end_time:
                slot_end_time = current_time + timedelta(minutes=30)

                is_available = True
                for appointment in appointments:
                    if (current_time < appointment.end_time and
                        slot_end_time > appointment.start_time):
                        is_available = False
                        break

                if is_available:
                    slots.append({
                        "start_time": current_time.isoformat(),
                        "end_time": slot_end_time.isoformat(),
                        "is_available": True
                    })

                current_time = slot_end_time

        return slots

doctor = CRUDDoctor(Doctor)
