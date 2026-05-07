from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.crud_department import department
from app.crud.crud_hospital import hospital
from app.schemas.department import Department, DepartmentCreate, DepartmentUpdate
from app.schemas.user import User
from app.db.session import get_db

router = APIRouter()


@router.get("/hospital/{hospital_id}", response_model=List[Department])
def read_departments_by_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all departments for a hospital.
    """
    hospital_obj = hospital.get(db, id=hospital_id)
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return department.get_by_hospital(db, hospital_id=hospital_id, skip=skip, limit=limit)


@router.get("/{id}", response_model=Department)
def read_department(
    id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get department by ID.
    """
    dept = department.get(db, id=id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.post("/", response_model=Department)
def create_department(
    *,
    db: Session = Depends(get_db),
    department_in: DepartmentCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new department for a hospital.
    Only hospital owner or admin can create departments.
    """
    hospital_obj = hospital.get(db, id=department_in.hospital_id)
    if not hospital_obj:
        raise HTTPException(status_code=404, detail="Hospital not found")

    if current_user.role != "admin" and hospital_obj.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check for duplicate department name in same hospital
    existing = department.get_by_name_and_hospital(
        db, name=department_in.name, hospital_id=department_in.hospital_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This department already exists in the hospital.",
        )

    return department.create(db, obj_in=department_in)


@router.put("/{id}", response_model=Department)
def update_department(
    *,
    db: Session = Depends(get_db),
    id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a department.
    """
    dept = department.get(db, id=id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    hospital_obj = hospital.get(db, id=dept.hospital_id)
    if current_user.role != "admin" and hospital_obj.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return department.update(db, db_obj=dept, obj_in=department_in)


@router.delete("/{id}", response_model=Department)
def delete_department(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a department.
    """
    dept = department.get(db, id=id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    hospital_obj = hospital.get(db, id=dept.hospital_id)
    if current_user.role != "admin" and hospital_obj.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return department.remove(db, id=id)
