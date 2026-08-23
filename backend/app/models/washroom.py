from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from .database import Base

class Washroom(Base):
    __tablename__ = "washrooms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    feedback = relationship("WashroomFeedback", back_populates="washroom")

class WashroomFeedback(Base):
    __tablename__ = "washroom_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    washroom_id = Column(String, ForeignKey("washrooms.id"), nullable=False)
    
    is_open = Column(Boolean, nullable=True)
    cleanliness = Column(String, nullable=True) # Clean, Average, Dirty
    safety = Column(String, nullable=True) # Safe, Concern, Unsafe
    accessible = Column(Boolean, nullable=True)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    washroom = relationship("Washroom", back_populates="feedback")
