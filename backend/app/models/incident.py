from sqlalchemy import Column, Integer, String, Float, DateTime
from app.models.database import Base
from datetime import datetime

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(String, index=True) # Nearest route segment
    event_type = Column(String, index=True)
    severity = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    active = Column(Integer, default=1)
    description = Column(String, nullable=True)
