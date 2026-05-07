from typing import Optional
from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models import Address
from app.schemas.address import AddressCreate, AddressUpdate


class CRUDAddress(CRUDBase[Address, AddressCreate, AddressUpdate]):
    def create_address(self, db: Session, *, obj_in: AddressCreate) -> Address:
        db_obj = Address(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


address = CRUDAddress(Address)
