from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    image = Column(String)
    port = Column(Integer)
    status = Column(String, default="running")
    created_at = Column(DateTime, default=datetime.utcnow)