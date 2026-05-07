"""
Public booking API routes.
These endpoints power the hospital-specific booking flow.
The /api/booking/{slug} endpoint is public (no auth) to show hospital info.
Other endpoints require patient authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, timedelta

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models import Hospital, Doctor, Patient, Appointment, User, HospitalPatient
from app.crud.crud_hospital import hospital as crud_hospital
from app.crud.crud_user import user as crud_user

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────

class PatientOnboardRequest(BaseModel):
    """Minimal patient registration — only name is required."""
    first_name: str = Field(..., examples=["Rahul"])
    last_name: str = Field(..., examples=["Kumar"])
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, examples=["male"])
    blood_group: Optional[str] = Field(None, examples=["B+"])
    address: Optional[str] = None


class BookAppointmentRequest(BaseModel):
    doctor_id: int
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    appointment_type: Optional[str] = Field("in_person", examples=["in_person"])


# ─── Public: Hospital info by slug ────────────────────────────

@router.get("/{slug}")
def get_hospital_by_slug(slug: str, db: Session = Depends(get_db)):
    """
    Public endpoint — returns hospital info for the booking page.
    No authentication required.
    """
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    if hospital.status != "verified" or not hospital.is_active:
        raise HTTPException(status_code=403, detail="Hospital is not accepting bookings")

    return {
        "id": hospital.id,
        "name": hospital.name,
        "booking_slug": hospital.booking_slug,
        "hospital_type": hospital.hospital_type,
        "phone": hospital.phone,
        "email": hospital.email,
        "description": hospital.description,
        "logo_url": hospital.logo_url,
    }


@router.get("/{slug}/doctors")
def get_hospital_doctors(slug: str, db: Session = Depends(get_db)):
    """
    Public endpoint — returns active doctors of a hospital.
    """
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    doctors = db.query(Doctor).filter(
        Doctor.hospital_id == hospital.id,
        Doctor.is_active == True,
    ).all()

    return [
        {
            "id": d.id,
            "first_name": d.first_name,
            "last_name": d.last_name,
            "specialization": d.specialization,
            "qualification": d.qualification,
            "experience_years": d.experience_years,
            "fee": d.fee,
            "languages": d.languages,
        }
        for d in doctors
    ]

@router.get("/{slug}/doctors/{doctor_id}/slots")
def get_available_slots(slug: str, doctor_id: int, date: date, db: Session = Depends(get_db)):
    """
    Returns a list of available time slots for a doctor on a specific date,
    respecting hospital global settings and existing bookings.
    """
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id, Doctor.hospital_id == hospital.id, Doctor.is_active == True
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # 1. Check if the day is a working day for the hospital
    day_of_week = str(date.weekday())
    working_days = hospital.working_days.split(",") if hospital.working_days else []
    if day_of_week not in working_days:
        return []

    # 2. Get all booked appointments for that doctor on that date
    today_start = datetime.combine(date, datetime.min.time())
    today_end = datetime.combine(date, datetime.max.time())
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.start_time >= today_start,
        Appointment.start_time <= today_end,
        Appointment.status != "cancelled"
    ).all()

    booked_times = [appt.start_time.time() for appt in appointments]

    # 3. Generate slots
    slots = []
    current_time = datetime.combine(date, hospital.working_hours_start)
    end_datetime = datetime.combine(date, hospital.working_hours_end)
    
    lunch_start = datetime.combine(date, hospital.lunch_break_start) if hospital.lunch_break_start else None
    lunch_end = datetime.combine(date, hospital.lunch_break_end) if hospital.lunch_break_end else None

    slot_duration = timedelta(minutes=hospital.slot_duration_minutes)

    while current_time + slot_duration <= end_datetime:
        slot_time = current_time.time()
        
        # Check lunch break
        is_during_lunch = False
        if lunch_start and lunch_end:
            if current_time >= lunch_start and current_time < lunch_end:
                is_during_lunch = True
        
        if not is_during_lunch and slot_time not in booked_times:
            # Also, don't return past slots if the date is today
            if date == datetime.today().date() and current_time < datetime.now():
                pass
            else:
                slots.append(slot_time.strftime("%H:%M"))
        
        current_time += slot_duration

    return slots


# ─── Patient: Profile check & onboarding ─────────────────────

@router.get("/{slug}/me")
def get_my_patient_profile(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if the logged-in user has a patient profile and is linked to this hospital.
    Returns patient profile if exists, or signals that onboarding is needed.
    """
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Find patient by user's phone number
    patient = db.query(Patient).filter(
        Patient.phone == current_user.phone_number
    ).first()

    if not patient:
        return {"needs_onboarding": True, "patient": None, "hospital_name": hospital.name}

    # Ensure patient is linked to this hospital
    crud_hospital.link_patient(db, hospital_id=hospital.id, patient_id=patient.id)

    return {
        "needs_onboarding": False,
        "patient": {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "phone": patient.phone,
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
        },
        "hospital_name": hospital.name,
    }


@router.post("/{slug}/onboard")
def onboard_patient(
    slug: str,
    data: PatientOnboardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update patient profile and link to hospital.
    Called after OTP login for new patients.
    """
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Check if patient already exists with this phone
    patient = db.query(Patient).filter(
        Patient.phone == current_user.phone_number
    ).first()

    # Handle address
    address_id = None
    if data.address:
        from app.models import Address
        new_address = Address(line1=data.address, city="N/A", state="N/A", pincode="000000")
        db.add(new_address)
        db.flush()
        address_id = new_address.id

    if patient:
        # Update existing patient details
        patient.first_name = data.first_name
        patient.last_name = data.last_name
        if data.date_of_birth:
            patient.date_of_birth = data.date_of_birth
        if data.gender:
            patient.gender = data.gender
        if data.blood_group:
            patient.blood_group = data.blood_group
        if address_id:
            patient.address_id = address_id
    else:
        # Create new patient
        patient = Patient(
            first_name=data.first_name,
            last_name=data.last_name,
            phone=current_user.phone_number,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_group=data.blood_group,
            email=current_user.email,
            address_id=address_id,
        )
        db.add(patient)

    db.commit()
    db.refresh(patient)

    # Update user reference_id to point to patient
    current_user.reference_id = patient.id
    db.commit()

    # Link patient to hospital
    crud_hospital.link_patient(db, hospital_id=hospital.id, patient_id=patient.id)

    return {
        "message": "Patient profile created successfully",
        "patient": {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "phone": patient.phone,
        },
    }


# ─── Patient: Book appointment ───────────────────────────────

@router.post("/{slug}/appointments")
def book_appointment(
    slug: str,
    data: BookAppointmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book an appointment at this specific hospital."""
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Get patient profile
    patient = db.query(Patient).filter(Patient.phone == current_user.phone_number).first()
    if not patient:
        raise HTTPException(status_code=400, detail="Please complete your profile first")

    # Verify doctor belongs to this hospital
    doctor = db.query(Doctor).filter(
        Doctor.id == data.doctor_id,
        Doctor.hospital_id == hospital.id,
        Doctor.is_active == True,
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found at this hospital")

    # Implement preferred time nearest-slot logic
    req_date = data.start_time.date()
    preferred_time = data.start_time.time()

    # 1. Validate working days
    day_of_week = str(req_date.weekday())
    working_days = hospital.working_days.split(",") if hospital.working_days else []
    if day_of_week not in working_days:
        raise HTTPException(status_code=400, detail="Hospital is closed on this day")
        
    # 2. Get booked appointments for that doctor on that date
    today_start = datetime.combine(req_date, datetime.min.time())
    today_end = datetime.combine(req_date, datetime.max.time())
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == data.doctor_id,
        Appointment.start_time >= today_start,
        Appointment.start_time <= today_end,
        Appointment.status != "cancelled"
    ).all()
    booked_times = [appt.start_time.time() for appt in appointments]

    # 3. Find the exact slot or the nearest available slot >= preferred_time
    current_time = datetime.combine(req_date, hospital.working_hours_start)
    end_datetime = datetime.combine(req_date, hospital.working_hours_end)
    
    lunch_start = datetime.combine(req_date, hospital.lunch_break_start) if hospital.lunch_break_start else None
    lunch_end = datetime.combine(req_date, hospital.lunch_break_end) if hospital.lunch_break_end else None
    slot_duration = timedelta(minutes=hospital.slot_duration_minutes)

    found_slot = None
    while current_time + slot_duration <= end_datetime:
        slot_time = current_time.time()
        
        is_during_lunch = False
        if lunch_start and lunch_end:
            if current_time >= lunch_start and current_time < lunch_end:
                is_during_lunch = True
                
        if not is_during_lunch and slot_time not in booked_times:
            # Check if this slot is valid (>= preferred_time, and if today, >= now)
            if req_date == datetime.today().date() and current_time < datetime.now():
                pass
            elif slot_time >= preferred_time:
                found_slot = current_time
                break
                
        current_time += slot_duration

    if not found_slot:
        raise HTTPException(status_code=400, detail="No schedule is available for the rest of today. Please book an appointment for the next day.")

    actual_start_time = found_slot
    actual_end_time = found_slot + slot_duration

    # Generate token number for the day
    token_count = len(appointments)

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=data.doctor_id,
        hospital_id=hospital.id,
        start_time=actual_start_time,
        end_time=actual_end_time,
        reason=data.reason,
        appointment_type=data.appointment_type or "in_person",
        status="scheduled",
        token_number=token_count + 1,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return {
        "message": "Appointment booked successfully",
        "appointment": {
            "id": appointment.id,
            "token_number": appointment.token_number,
            "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}",
            "specialization": doctor.specialization,
            "start_time": appointment.start_time.replace(tzinfo=None).isoformat(),
            "status": appointment.status,
            "hospital_name": hospital.name,
        },
    }


# ─── Patient: My appointments at this hospital ───────────────

@router.get("/{slug}/appointments")
def get_my_appointments(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current patient's appointments at this hospital."""
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    patient = db.query(Patient).filter(Patient.phone == current_user.phone_number).first()
    if not patient:
        return []

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.hospital_id == hospital.id,
    ).order_by(Appointment.start_time.desc()).all()

    results = []
    for appt in appointments:
        doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        results.append({
            "id": appt.id,
            "token_number": appt.token_number,
            "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else "N/A",
            "specialization": doctor.specialization if doctor else "N/A",
            "start_time": appt.start_time.replace(tzinfo=None).isoformat(),
            "end_time": appt.end_time.replace(tzinfo=None).isoformat(),
            "status": appt.status,
            "appointment_type": appt.appointment_type,
            "reason": appt.reason,
        })

    return results

class UpdateAppointmentRequest(BaseModel):
    status: Optional[str] = None  # cancelled
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

@router.put("/{slug}/appointments/{appointment_id}")
def update_appointment(
    slug: str,
    appointment_id: int,
    data: UpdateAppointmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update or cancel a patient's appointment."""
    hospital = crud_hospital.get_by_slug(db, slug=slug)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    patient = db.query(Patient).filter(Patient.phone == current_user.phone_number).first()
    if not patient:
        raise HTTPException(status_code=400, detail="Profile not found")

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == patient.id,
        Appointment.hospital_id == hospital.id,
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if data.status:
        appointment.status = data.status
    if data.start_time:
        appointment.start_time = data.start_time
    if data.end_time:
        appointment.end_time = data.end_time

    db.commit()
    db.refresh(appointment)
    
    return {"message": "Appointment updated successfully", "status": appointment.status}
