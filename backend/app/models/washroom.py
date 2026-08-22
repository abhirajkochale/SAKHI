from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base

class Washroom(Base):
    __tablename__ = "washrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    feedbacks = relationship("WashroomFeedback", back_populates="washroom", cascade="all, delete-orphan")


class WashroomFeedback(Base):
    __tablename__ = "washroom_feedback"

    id = Column(Integer, primary_key=True, index=True)
    washroom_id = Column(Integer, ForeignKey("washrooms.id"))
    is_open = Column(Boolean, nullable=False)
    cleanliness = Column(String, nullable=False) # Clean, Average, Dirty
    safety = Column(String, nullable=False) # Safe, Concern, Unsafe
    accessible = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    washroom = relationship("Washroom", back_populates="feedbacks")
