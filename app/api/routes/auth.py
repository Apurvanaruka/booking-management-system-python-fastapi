from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.core.otp_service import create_otp_request, verify_otp
from app.crud.crud_user import user
from app.crud.crud_patient import patient
from app.crud.crud_hospital import hospital as hospital_crud
from app.crud.crud_address import address as address_crud
from app.schemas.user import (
    User, UserCreate, Token,
    OTPSendRequest, OTPSendResponse, OTPVerifyRequest, OTPVerifyResponse,
)
from app.schemas.hospital import HospitalRegistration
from app.schemas.patient import PatientCreate
from app.db.session import get_db
from pydantic import BaseModel, EmailStr

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr = "demo@example.com"
    password: str = "password123"

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "supersecret"}
        }


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Token login with email + password. Returns JWT access token.
    """
    user_obj = user.authenticate(
        db, email=login_data.email, password=login_data.password
    )
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user_obj.id, user_obj.role, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user (admin/staff/doctor).
    """
    if user_in.email:
        user_obj = user.get_by_email(db, email=user_in.email)
        if user_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

    existing_username = user.get_by_username(db, username=user_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )

    return user.create(db, obj_in=user_in)


@router.post("/register-hospital", response_model=User, status_code=status.HTTP_201_CREATED)
def register_hospital(
    *,
    db: Session = Depends(get_db),
    registration: HospitalRegistration,
) -> Any:
    """
    Register a new hospital with an admin account.
    Hospital will be in 'pending' status until admin approves.
    """
    # Check for existing email/username
    if user.get_by_email(db, email=registration.admin_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    if user.get_by_username(db, username=registration.admin_username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )
    if hospital_crud.get_by_email(db, email=registration.hospital_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A hospital with this email already exists.",
        )

    # Create admin user
    user_in = UserCreate(
        username=registration.admin_username,
        email=registration.admin_email,
        password=registration.admin_password,
        role="hospital",
        is_active=True,
        phone_number=registration.admin_phone,
    )
    admin_user = user.create(db, obj_in=user_in)

    # Create address if provided
    address_id = None
    if registration.address:
        addr_obj = address_crud.create_address(db, obj_in=registration.address)
        address_id = addr_obj.id

    # Create hospital
    from app.models import Hospital
    hospital_obj = Hospital(
        name=registration.hospital_name,
        hospital_type=registration.hospital_type.value,
        registration_number=registration.registration_number,
        phone=registration.hospital_phone,
        email=registration.hospital_email,
        description=registration.description,
        address_id=address_id,
        owner_user_id=admin_user.id,
        status="pending",
    )
    db.add(hospital_obj)
    db.commit()
    db.refresh(hospital_obj)

    # Link hospital to user
    admin_user.reference_id = hospital_obj.id
    db.commit()
    db.refresh(admin_user)

    return admin_user


# ─── OTP-Based Patient Authentication ──────────────────────────

@router.post("/send-otp", response_model=OTPSendResponse)
def send_otp(
    *,
    db: Session = Depends(get_db),
    otp_request: OTPSendRequest,
) -> Any:
    """
    Send OTP to a mobile number. Works for both new and existing patients.
    In dev mode, OTP is always '123456' and printed to console.
    """
    otp = create_otp_request(db, phone_number=otp_request.phone_number)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create OTP. Please try again.",
        )

    return OTPSendResponse(
        message="OTP sent successfully",
        phone_number=otp_request.phone_number,
        expires_in_seconds=settings.OTP_EXPIRY_MINUTES * 60,
    )


@router.post("/verify-otp", response_model=OTPVerifyResponse)
def verify_otp_endpoint(
    *,
    db: Session = Depends(get_db),
    otp_data: OTPVerifyRequest,
) -> Any:
    """
    Verify OTP and return JWT token.
    If the patient doesn't exist, auto-creates a new patient and user account.
    """
    is_valid = verify_otp(db, phone_number=otp_data.phone_number, otp_code=otp_data.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # Find existing user by phone
    user_obj = user.get_by_phone(db, phone_number=otp_data.phone_number)
    is_new_user = False

    if not user_obj:
        is_new_user = True

        # Create patient record
        patient_obj = patient.create(
            db,
            obj_in=PatientCreate(
                first_name="Patient",
                last_name="",
                phone=otp_data.phone_number,
            ),
        )

        # Create user account linked to patient
        user_in = UserCreate(
            username=f"patient_{otp_data.phone_number[-4:]}_{patient_obj.id}",
            role="patient",
            is_active=True,
            phone_number=otp_data.phone_number,
        )
        user_obj = user.create(db, obj_in=user_in)

        # Link user to patient
        user_obj.reference_id = patient_obj.id
        db.commit()
        db.refresh(user_obj)

    # Generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user_obj.id, user_obj.role, expires_delta=access_token_expires
    )

    return OTPVerifyResponse(
        access_token=access_token,
        token_type="bearer",
        is_new_user=is_new_user,
    )


@router.get("/me", response_model=User)
def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user
