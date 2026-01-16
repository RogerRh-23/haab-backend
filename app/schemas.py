from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ApplicationCreate(BaseModel):
    name: str
    image: str
    port: int

class ApplicationResponse(BaseModel):
    id: int
    name: str
    image: str
    port: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True