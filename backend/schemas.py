from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .models import JobStatus

class ScanJobBase(BaseModel):
    name: str

class ScanJobCreate(ScanJobBase):
    pass

class ScanJob(ScanJobBase):
    id: int
    status: JobStatus
    error_message: Optional[str] = None
    model_path: Optional[str] = None
    orthophoto_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True
