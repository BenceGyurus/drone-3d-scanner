import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from io import BytesIO

from .main import app
from . import database, models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[database.get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield

@patch("backend.main.processing.process_video_task")
def test_create_job(mock_task):
    video_content = b"fake_video_content"
    video_file = BytesIO(video_content)
    video_file.name = "test.mp4"
    
    response = client.post(
        "/jobs/",
        data={"name": "Test Scan"},
        files={"video": ("test.mp4", video_file, "video/mp4")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Scan"
    assert data["status"] == "PENDING"
    assert "id" in data
    mock_task.assert_called_once()

def test_create_job_invalid_format():
    video_content = b"fake_video_content"
    video_file = BytesIO(video_content)
    video_file.name = "test.txt"
    
    response = client.post(
        "/jobs/",
        data={"name": "Test Scan"},
        files={"video": ("test.txt", video_file, "text/plain")}
    )
    
    assert response.status_code == 400

@patch("backend.main.processing.process_video_task")
def test_get_jobs(mock_task):
    client.post(
        "/jobs/",
        data={"name": "Job 1"},
        files={"video": ("test.mp4", BytesIO(b"fake"), "video/mp4")}
    )
    client.post(
        "/jobs/",
        data={"name": "Job 2"},
        files={"video": ("test2.mp4", BytesIO(b"fake"), "video/mp4")}
    )
    
    response = client.get("/jobs/")
    assert response.status_code == 200
    assert len(response.json()) == 2

@patch("backend.main.processing.process_video_task")
def test_delete_job(mock_task):
    res = client.post(
        "/jobs/",
        data={"name": "Job to Delete"},
        files={"video": ("test.mp4", BytesIO(b"fake"), "video/mp4")}
    )
    job_id = res.json()["id"]
    
    del_res = client.delete(f"/jobs/{job_id}")
    assert del_res.status_code == 200
    
    get_res = client.get(f"/jobs/{job_id}")
    assert get_res.status_code == 404
