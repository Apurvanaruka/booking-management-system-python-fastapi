from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Shared properties
class MedicalRecordBase(BaseModel):
    patient_id: int = Field(..., examples=[1])
    appointment_id: Optional[int] = Field(None, examples=[1])
    diagnosis: Optional[str] = Field(None, examples=["Type 2 Diabetes"])
    treatment: Optional[str] = Field(None, examples=["Metformin 500mg"])
    prescription: Optional[str] = Field(None, examples=["Metformin 500mg, twice daily"])
    notes: Optional[str] = Field(None, examples=["Patient is showing improvement"])

# Properties to receive on medical record creation
class MedicalRecordCreate(MedicalRecordBase):
    pass

# Properties to receive on medical record update
class MedicalRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None

# Properties shared by models stored in DB
class MedicalRecordInDBBase(MedicalRecordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Properties to return to client
class MedicalRecord(MedicalRecordInDBBase):
    pass

# Properties stored in DB
class MedicalRecordInDB(MedicalRecordInDBBase):
    pass

