from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.crud_base import CRUDBase
from app.models import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_by_phone(self, db: Session, *, phone_number: str) -> Optional[User]:
        return db.query(User).filter(User.phone_number == phone_number).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password) if obj_in.password else None,
            role=obj_in.role.value if hasattr(obj_in.role, 'value') else obj_in.role,
            is_active=obj_in.is_active,
            reference_id=obj_in.reference_id,
            phone_number=obj_in.phone_number,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


user = CRUDUser(User)
