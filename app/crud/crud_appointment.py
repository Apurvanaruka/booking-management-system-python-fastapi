from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.crud_base import CRUDBase
from app.models import Appointment, Patient, Doctor
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentStatus

class CRUDAppointment(CRUDBase[Appointment, AppointmentCreate, AppointmentUpdate]):
    def get_by_patient(
        self, db: Session, *, patient_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        query = db.query(Appointment).filter(Appointment.patient_id == patient_id)

        if start_date:
            query = query.filter(Appointment.start_time >= start_date)
        if end_date:
            query = query.filter(Appointment.end_time <= end_date)

        return query.offset(skip).limit(limit).all()

    def get_by_doctor(
        self, db: Session, *, doctor_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        query = db.query(Appointment).filter(Appointment.doctor_id == doctor_id)

        if start_date:
            query = query.filter(Appointment.start_time >= start_date)
        if end_date:
            query = query.filter(Appointment.end_time <= end_date)

        return query.offset(skip).limit(limit).all()

    def get_with_details(self, db: Session, *, id: int) -> Optional[Dict[str, Any]]:
        result = db.query(
            Appointment,
            Patient.first_name.label("patient_first_name"),
            Patient.last_name.label("patient_last_name"),
            Doctor.first_name.label("doctor_first_name"),
            Doctor.last_name.label("doctor_last_name"),
            Doctor.specialization.label("doctor_specialization")
        ).join(
            Patient, Appointment.patient_id == Patient.id
        ).join(
            Doctor, Appointment.doctor_id == Doctor.id
        ).filter(
            Appointment.id == id
        ).first()

        if not result:
            return None

        appointment, patient_first_name, patient_last_name, doctor_first_name, doctor_last_name, doctor_specialization = result

        return {
            **appointment.__dict__,
            "patient_name": f"{patient_first_name} {patient_last_name}",
            "doctor_name": f"{doctor_first_name} {doctor_last_name}",
            "doctor_specialization": doctor_specialization
        }

    def get_multi_with_details(
        self, db: Session, *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = db.query(
            Appointment,
            Patient.first_name.label("patient_first_name"),
            Patient.last_name.label("patient_last_name"),
            Doctor.first_name.label("doctor_first_name"),
            Doctor.last_name.label("doctor_last_name"),
            Doctor.specialization.label("doctor_specialization")
        ).join(
            Patient, Appointment.patient_id == Patient.id
        ).join(
            Doctor, Appointment.doctor_id == Doctor.id
        )

        if start_date:
            query = query.filter(Appointment.start_time >= start_date)
        if end_date:
            query = query.filter(Appointment.end_time <= end_date)

        results = query.offset(skip).limit(limit).all()

        appointments = []
        for result in results:
            appointment, patient_first_name, patient_last_name, doctor_first_name, doctor_last_name, doctor_specialization = result

            appointments.append({
                **appointment.__dict__,
                "patient_name": f"{patient_first_name} {patient_last_name}",
                "doctor_name": f"{doctor_first_name} {doctor_last_name}",
                "doctor_specialization": doctor_specialization
            })

        return appointments

    def check_conflicts(
        self, db: Session, *,
        doctor_id: int,
        start_time: datetime,
        end_time: datetime,
        appointment_id: Optional[int] = None
    ) -> bool:
        """
        Check if there are any conflicting appointments for the doctor.
        If appointment_id is provided, exclude that appointment from the check.
        """
        query = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status != "cancelled",
            or_(
                and_(
                    Appointment.start_time <= start_time,
                    Appointment.end_time > start_time
                ),
                and_(
                    Appointment.start_time < end_time,
                    Appointment.end_time >= end_time
                ),
                and_(
                    Appointment.start_time >= start_time,
                    Appointment.end_time <= end_time
                )
            )
        )

        if appointment_id:
            query = query.filter(Appointment.id != appointment_id)

        return query.count() > 0

    def update_status(self, db: Session, *, id: int, status: AppointmentStatus) -> Appointment:
        appointment = self.get(db, id=id)
        if not appointment:
            return None

        appointment.status = status.value
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

appointment = CRUDAppointment(Appointment)
