from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_admin
from app.crud.crud_hospital import hospital
from app.crud.crud_address import address
from app.schemas.hospital import (
    Hospital, HospitalCreate, HospitalUpdate,
    HospitalWithAddress, HospitalVerify,
)
from app.schemas.user import User
from app.db.session import get_db

router = APIRouter()


@router.get("/", response_model=List[Hospital])
def read_hospitals(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    verified_only: bool = True,
) -> Any:
    """
    Retrieve hospitals. By default only returns verified hospitals.
    Admin can see all by setting verified_only=False.
    """
    if verified_only:
        return hospital.get_verified(db, skip=skip, limit=limit)
    return hospital.get_multi(db, skip=skip, limit=limit)


@router.get("/pending", response_model=List[Hospital])
def read_pending_hospitals(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Get hospitals pending admin approval. Admin only.
    """
    return hospital.get_pending(db, skip=skip, limit=limit)


@router.get("/search", response_model=List[Hospital])
def search_hospitals_by_city(
    city: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Search verified hospitals by city name.
    """
    return hospital.search_by_city(db, city=city, skip=skip, limit=limit)


@router.get("/my", response_model=List[Hospital])
def read_my_hospitals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get hospitals owned by the current user.
    """
    return hospital.get_by_owner(db, owner_user_id=current_user.id)


@router.get("/{id}", response_model=HospitalWithAddress)
def read_hospital(
    *,
    db: Session = Depends(get_db),
    id: int,
) -> Any:
    """
    Get hospital by ID with address details.
    """
    hospital_obj = hospital.get(db, id=id)
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital_obj


@router.post("/", response_model=Hospital)
def create_hospital(
    *,
    db: Session = Depends(get_db),
    hospital_in: HospitalCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new hospital. Will be in 'pending' status until admin approves.
    """
    existing = hospital.get_by_email(db, email=hospital_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A hospital with this email already exists.",
        )

    # Create address if provided
    address_id = None
    if hospital_in.address:
        addr_obj = address.create_address(db, obj_in=hospital_in.address)
        address_id = addr_obj.id

    hospital_obj = hospital.create_with_owner(
        db, obj_in=hospital_in, owner_user_id=current_user.id, address_id=address_id
    )
    return hospital_obj


@router.put("/{id}", response_model=Hospital)
def update_hospital(
    *,
    db: Session = Depends(get_db),
    id: int,
    hospital_in: HospitalUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a hospital. Only owner or admin can update.
    """
    hospital_obj = hospital.get(db, id=id)
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")

    if current_user.role != "admin" and hospital_obj.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    hospital_obj = hospital.update(db, db_obj=hospital_obj, obj_in=hospital_in)
    return hospital_obj


@router.put("/{id}/verify", response_model=Hospital)
def verify_hospital(
    *,
    db: Session = Depends(get_db),
    id: int,
    verify_in: HospitalVerify,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Verify/approve/reject a hospital. Admin only.
    """
    hospital_obj = hospital.verify(
        db, id=id, status=verify_in.status.value, notes=verify_in.verification_notes
    )
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital_obj


@router.delete("/{id}", response_model=Hospital)
def delete_hospital(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Delete a hospital. Admin only.
    """
    hospital_obj = hospital.get(db, id=id)
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")
    hospital_obj = hospital.remove(db, id=id)
    return hospital_obj
