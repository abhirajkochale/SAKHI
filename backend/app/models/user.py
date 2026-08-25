from sqlalchemy import Column, Integer, String, DateTime, Uuid
from app.models.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=False), primary_key=True, index=True) # Supabase UUID
    email = Column(String, unique=True, index=True, nullable=True)
    display_name = Column(String, nullable=True)
    identity_status = Column(String, default="NORMAL") # NORMAL or VERIFIED
    identity_provider = Column(String, nullable=True) # e.g. "google", "aadhaar"
    identity_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
