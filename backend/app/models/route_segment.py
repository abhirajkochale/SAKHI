from sqlalchemy import Column, Integer, String, Float, DateTime
from app.models.database import Base
from datetime import datetime

class PersistentRouteSegment(Base):
    """
    Stores historical baseline risk scores for a specific geographic segment.
    """
    __tablename__ = "route_segments"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(String, unique=True, index=True)
    base_risk_score = Column(Float, default=0.0)
    base_confidence_score = Column(Float, default=1.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
