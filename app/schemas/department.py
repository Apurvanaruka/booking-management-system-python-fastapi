from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DepartmentBase(BaseModel):
    name: str = Field(..., examples=["General Medicine"])
    description: Optional[str] = Field(None, examples=["General health consultations"])
    hospital_id: int = Field(..., examples=[1])


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentInDBBase(DepartmentBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Department(DepartmentInDBBase):
    pass
