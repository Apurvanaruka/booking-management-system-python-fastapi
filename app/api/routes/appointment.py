from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.crud.crud_appointment import appointment
from app.crud.crud_doctor import doctor
from app.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentDetail, AppointmentStatus
from app.schemas.user import User
from app.db.session import get_db
from app.core.notifications import send_appointment_notification

router = APIRouter()


@router.get("/", response_model=List[AppointmentDetail])
def read_appointments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve appointments with optional date filtering.
    """
    # If user is a patient, only show their appointments
    if current_user.role == "patient":
        appointments = appointment.get_by_patient(
            db, patient_id=current_user.reference_id,
            start_date=start_date, end_date=end_date,
            skip=skip, limit=limit
        )
    # If user is a doctor, only show their appointments
    elif current_user.role == "doctor":
        appointments = appointment.get_by_doctor(
            db, doctor_id=current_user.reference_id,
            start_date=start_date, end_date=end_date,
            skip=skip, limit=limit
        )
    # Admin, hospital, and staff can see all appointments
    else:
        appointments = appointment.get_multi_with_details(
            db, start_date=start_date, end_date=end_date,
            skip=skip, limit=limit
        )

    return appointments


@router.post("/", response_model=Appointment)
def create_appointment(
    *,
    db: Session = Depends(get_db),
    appointment_in: AppointmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new appointment.
    """
    # Check if the doctor is available at the requested time
    is_available = doctor.check_availability(
        db,
        doctor_id=appointment_in.doctor_id,
        start_time=appointment_in.start_time,
        end_time=appointment_in.end_time
    )

    if not is_available:
        raise HTTPException(
            status_code=400,
            detail="Doctor is not available at the requested time"
        )

    # Check for overlapping appointments
    has_conflict = appointment.check_conflicts(
        db,
        doctor_id=appointment_in.doctor_id,
        start_time=appointment_in.start_time,
        end_time=appointment_in.end_time,
        appointment_id=None
    )

    if has_conflict:
        raise HTTPException(
            status_code=400,
            detail="There is a scheduling conflict with another appointment"
        )

    # Create the appointment
    appointment_obj = appointment.create(db, obj_in=appointment_in)

    # Send notification in background
    background_tasks.add_task(
        send_appointment_notification,
        appointment_id=appointment_obj.id,
        notification_type="created"
    )

    return appointment_obj


@router.get("/{id}", response_model=AppointmentDetail)
def read_appointment(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get appointment by ID.
    """
    appointment_obj = appointment.get_with_details(db, id=id)
    if not appointment_obj:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Check permissions
    if current_user.role == "patient" and current_user.reference_id != appointment_obj.get("patient_id"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if current_user.role == "doctor" and current_user.reference_id != appointment_obj.get("doctor_id"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return appointment_obj


@router.put("/{id}", response_model=Appointment)
def update_appointment(
    *,
    db: Session = Depends(get_db),
    id: int,
    appointment_in: AppointmentUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update an appointment.
    """
    appointment_obj = appointment.get(db, id=id)
    if not appointment_obj:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Check permissions
    if current_user.role == "patient" and current_user.reference_id != appointment_obj.patient_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # If updating time, check for availability and conflicts
    if appointment_in.start_time and appointment_in.end_time:
        is_available = doctor.check_availability(
            db,
            doctor_id=appointment_obj.doctor_id,
            start_time=appointment_in.start_time,
            end_time=appointment_in.end_time
        )

        if not is_available:
            raise HTTPException(
                status_code=400,
                detail="Doctor is not available at the requested time"
            )

        has_conflict = appointment.check_conflicts(
            db,
            doctor_id=appointment_obj.doctor_id,
            start_time=appointment_in.start_time,
            end_time=appointment_in.end_time,
            appointment_id=id
        )

        if has_conflict:
            raise HTTPException(
                status_code=400,
                detail="There is a scheduling conflict with another appointment"
            )

    # Update the appointment
    appointment_obj = appointment.update(
        db, db_obj=appointment_obj, obj_in=appointment_in)

    # Send notification in background
    background_tasks.add_task(
        send_appointment_notification,
        appointment_id=appointment_obj.id,
        notification_type="updated"
    )

    return appointment_obj


@router.delete("/{id}", response_model=Appointment)
def delete_appointment(
    *,
    db: Session = Depends(get_db),
    id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete an appointment.
    """
    appointment_obj = appointment.get(db, id=id)
    if not appointment_obj:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient_id = appointment_obj.patient_id
    doctor_id = appointment_obj.doctor_id
    appointment_time = appointment_obj.start_time

    appointment_obj = appointment.remove(db, id=id)

    background_tasks.add_task(
        send_appointment_notification,
        appointment_id=id,
        notification_type="cancelled",
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_time=appointment_time
    )

    return appointment_obj


@router.put("/{id}/status", response_model=Appointment)
def update_appointment_status(
    *,
    db: Session = Depends(get_db),
    id: int,
    status: AppointmentStatus,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update appointment status.
    """
    appointment_obj = appointment.get(db, id=id)
    if not appointment_obj:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment_obj = appointment.update_status(db, id=id, status=status)

    background_tasks.add_task(
        send_appointment_notification,
        appointment_id=appointment_obj.id,
        notification_type="status_updated",
        status=status.value
    )

    return appointment_obj


@router.get("/doctor/{doctor_id}/available-slots", response_model=List[dict])
def get_available_slots(
    *,
    db: Session = Depends(get_db),
    doctor_id: int,
    date: datetime = Query(...),
) -> Any:
    """
    Get available appointment slots for a doctor on a specific date.
    """
    available_slots = doctor.get_available_slots(
        db,
        doctor_id=doctor_id,
        date=date
    )

    return available_slots
