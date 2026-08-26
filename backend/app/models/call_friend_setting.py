from sqlalchemy import Column, String, Integer, DateTime, Uuid, ForeignKey
from app.models.database import Base
from datetime import datetime
import uuid

class CallFriendSetting(Base):
    __tablename__ = "call_friend_settings"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    caller_name = Column(String, nullable=False, default="Bro")
    language_code = Column(String, nullable=False, default="en-IN")
    voice_gender = Column(String, nullable=False, default="Male")
    speaker = Column(String, nullable=False, default="shubh")
    script = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)