from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from .database import Base
import enum

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXTRACTING_FRAMES = "EXTRACTING_FRAMES"
    UPLOADING_TO_ODM = "UPLOADING_TO_ODM"
    PROCESSING_ODM = "PROCESSING_ODM"
    DOWNLOADING_RESULTS = "DOWNLOADING_RESULTS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    error_message = Column(String, nullable=True)
    
    # Store ODM task id
    odm_task_id = Column(String, nullable=True)
    
    # Paths to the assets
    model_path = Column(String, nullable=True)
    orthophoto_path = Column(String, nullable=True)
    
    # Optional GPS coordinates extracted from images
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
