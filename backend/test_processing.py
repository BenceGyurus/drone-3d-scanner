import asyncio
import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import models
from models import Base, ScanJob, JobStatus
from processing import process_video_task

@pytest.fixture
def mock_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    
    # Create a dummy job
    job = ScanJob(name="Test Job", status=JobStatus.PENDING)
    session.add(job)
    session.commit()
    
    yield session
    session.close()

@patch("processing.database.SessionLocal")
@patch("processing.ffmpeg")
@patch("processing.subprocess.run")
@patch("processing.shutil.rmtree")
@patch("processing.shutil.copy")
@patch("processing.os.remove")
@patch("processing.os.listdir")
@patch("processing.os.path.isdir")
@patch("processing.os.path.exists")
@patch("processing.os.makedirs")
@pytest.mark.asyncio
async def test_process_video_task(
    mock_makedirs, mock_exists, mock_isdir, mock_listdir, mock_remove, mock_copy, 
    mock_rmtree, mock_subprocess, mock_ffmpeg, mock_session_local, mock_db_session
):
    # Setup DB mock
    mock_session_local.return_value = mock_db_session
    
    job_id = 1
    video_path = "/fake/video.mp4"
    
    # Mock os.listdir to return some fake images so extraction doesn't fail
    # It gets called twice: once for images, once for cleanup
    def listdir_side_effect(path):
        if "images" in path:
            return ["image_0001.jpg"]
        return ["odm_texturing"]
    mock_listdir.side_effect = listdir_side_effect
    
    # Mock os.path.exists to simulate ODM outputs existing
    mock_exists.return_value = True
    
    # Mock os.path.isdir so cleanup removes folders
    mock_isdir.return_value = True
    
    # Mock subprocess success
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process
    
    # Mock ffmpeg success
    mock_ffmpeg.input.return_value.filter.return_value.output.return_value.run.return_value = (b"", b"")
    
    # Run the task
    await process_video_task(job_id, video_path)
    
    # Assertions
    # 1. FFmpeg was called
    mock_ffmpeg.input.assert_called_with(video_path)
    
    # 2. Subprocess (ODM) was called
    assert mock_subprocess.called
    cmd = mock_subprocess.call_args[0][0]
    assert "docker" in cmd
    assert "opendronemap/odm" in cmd
    
    # 3. Cleanup happened
    mock_remove.assert_called_with(video_path)
    assert mock_rmtree.called
    
    # 4. Job status is COMPLETED
    job = mock_db_session.query(ScanJob).filter(ScanJob.id == job_id).first()
    assert job.status == JobStatus.COMPLETED
    assert job.latitude is not None
    assert job.longitude is not None
    assert job.model_path is not None
