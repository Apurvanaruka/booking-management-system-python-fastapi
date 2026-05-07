"""
Admin-only API routes for system management.
All endpoints require admin role authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.db.session import get_db
from app.api.deps import get_current_admin
from app.models import User, Hospital, Doctor, Patient, Appointment, Department
from app.crud.crud_user import user as crud_user
from app.crud.crud_hospital import hospital as crud_hospital

router = APIRouter()


# ─── Dashboard Stats ─────────────────────────────────────────
@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Get overall system statistics for the admin dashboard."""
    total_hospitals = db.query(func.count(Hospital.id)).scalar()
    pending_hospitals = db.query(func.count(Hospital.id)).filter(Hospital.status == "pending").scalar()
    verified_hospitals = db.query(func.count(Hospital.id)).filter(Hospital.status == "verified").scalar()
    total_doctors = db.query(func.count(Doctor.id)).scalar()
    total_patients = db.query(func.count(Patient.id)).scalar()
    total_appointments = db.query(func.count(Appointment.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

    return {
        "hospitals": {
            "total": total_hospitals,
            "pending": pending_hospitals,
            "verified": verified_hospitals,
        },
        "doctors": {"total": total_doctors},
        "patients": {"total": total_patients},
        "appointments": {"total": total_appointments},
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
        },
    }


# ─── Hospital Management ─────────────────────────────────────
@router.get("/hospitals")
def list_all_hospitals(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, verified, rejected, suspended"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """List all hospitals with optional status filter."""
    query = db.query(Hospital)
    if status_filter:
        query = query.filter(Hospital.status == status_filter)
    return query.order_by(Hospital.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/hospitals/{hospital_id}")
def get_hospital_detail(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Get detailed info of a hospital including owner details."""
    hospital = crud_hospital.get(db, id=hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    owner = crud_user.get(db, id=hospital.owner_user_id)
    departments = db.query(Department).filter(Department.hospital_id == hospital_id).all()
    doctors = db.query(Doctor).filter(Doctor.hospital_id == hospital_id).all()

    return {
        "hospital": hospital,
        "owner": owner,
        "departments": departments,
        "doctors": doctors,
        "department_count": len(departments),
        "doctor_count": len(doctors),
    }


@router.put("/hospitals/{hospital_id}/verify")
def verify_hospital(
    hospital_id: int,
    status: str = Query(..., description="verified, rejected, suspended"),
    verification_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Approve, reject, or suspend a hospital."""
    valid_statuses = ["verified", "rejected", "suspended"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")

    hospital = crud_hospital.verify(db, id=hospital_id, status=status, notes=verification_notes)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital


@router.put("/hospitals/{hospital_id}/toggle-active")
def toggle_hospital_active(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Activate or deactivate a hospital."""
    hospital = crud_hospital.get(db, id=hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    hospital.is_active = not hospital.is_active
    db.commit()
    db.refresh(hospital)
    return {"id": hospital.id, "name": hospital.name, "is_active": hospital.is_active}


# ─── User Management ─────────────────────────────────────────
@router.get("/users")
def list_all_users(
    role: Optional[str] = Query(None, description="Filter by role: admin, doctor, patient, staff, hospital"),
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """List all users with optional role and active status filter."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Activate or deactivate a user account."""
    target_user = crud_user.get(db, id=user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deactivating themselves
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    target_user.is_active = not target_user.is_active
    db.commit()
    db.refresh(target_user)
    return {
        "id": target_user.id,
        "username": target_user.username,
        "is_active": target_user.is_active,
    }


@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    new_role: str = Query(..., description="New role: admin, doctor, patient, staff, hospital"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Change a user's role."""
    valid_roles = ["admin", "doctor", "patient", "staff", "hospital"]
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {valid_roles}")

    target_user = crud_user.get(db, id=user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.role = new_role
    db.commit()
    db.refresh(target_user)
    return target_user


# ─── Doctor Management ────────────────────────────────────────
@router.get("/doctors")
def list_all_doctors(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """List all doctors across all hospitals."""
    query = db.query(Doctor)
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.put("/doctors/{doctor_id}/toggle-active")
def toggle_doctor_active(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Activate or deactivate a doctor."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_active = not doctor.is_active
    db.commit()
    db.refresh(doctor)
    return {"id": doctor.id, "name": f"{doctor.first_name} {doctor.last_name}", "is_active": doctor.is_active}


# ─── Patient Management ──────────────────────────────────────
@router.get("/patients")
def list_all_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """List all patients across the system."""
    return db.query(Patient).offset(skip).limit(limit).all()


# ─── Appointment Management ───────────────────────────────────
@router.get("/appointments")
def list_all_appointments(
    status_filter: Optional[str] = Query(None, description="Filter by status: scheduled, confirmed, cancelled, completed"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """List all appointments across the system."""
    query = db.query(Appointment)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    return query.order_by(Appointment.created_at.desc()).offset(skip).limit(limit).all()


@router.put("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    new_status: str = Query(..., description="New status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Admin override for appointment status."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = new_status
    db.commit()
    db.refresh(appointment)
    return appointment
