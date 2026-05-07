from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.models.base import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    line1 = Column(String, nullable=False)
    line2 = Column(String, nullable=True)
    landmark = Column(String, nullable=True)
    city = Column(String, nullable=False, index=True)
    district = Column(String, nullable=True, index=True)
    state = Column(String, nullable=False, index=True)
    pincode = Column(String, nullable=False, index=True)
    country = Column(String, default="India", index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address_type = Column(String, nullable=True)  # home, office, hospital

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
