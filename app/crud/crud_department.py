from typing import Optional, List
from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    def get_by_hospital(self, db: Session, *, hospital_id: int, skip: int = 0, limit: int = 100) -> List[Department]:
        return db.query(Department).filter(
            Department.hospital_id == hospital_id,
            Department.is_active == True
        ).offset(skip).limit(limit).all()

    def get_by_name_and_hospital(self, db: Session, *, name: str, hospital_id: int) -> Optional[Department]:
        return db.query(Department).filter(
            Department.name == name,
            Department.hospital_id == hospital_id
        ).first()


department = CRUDDepartment(Department)
