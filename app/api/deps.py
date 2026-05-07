from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.user import TokenPayload, UserRole
from app.crud.crud_user import user

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="JWT",
    description="JWT token authentication"
)

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user_obj = user.get(db, id=token_data.sub)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    if not user_obj.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user_obj

def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin(current_user = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_hospital_owner(current_user = Depends(get_current_user)):
    """Allow hospital owners and admins."""
    if current_user.role not in [UserRole.HOSPITAL.value, UserRole.HOSPITAL, UserRole.ADMIN.value, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_doctor(current_user = Depends(get_current_user)):
    if current_user.role not in [UserRole.DOCTOR.value, UserRole.DOCTOR, UserRole.ADMIN.value, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_staff(current_user = Depends(get_current_user)):
    allowed = [
        UserRole.STAFF.value, UserRole.STAFF,
        UserRole.ADMIN.value, UserRole.ADMIN,
        UserRole.DOCTOR.value, UserRole.DOCTOR,
    ]
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user
