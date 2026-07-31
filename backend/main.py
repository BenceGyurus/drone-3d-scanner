from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
import shutil
import uuid

from . import models, schemas, database, processing

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Drone 3D Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(os.path.join(database.os.getcwd(), "data", "public"), exist_ok=True)
os.makedirs(os.path.join(database.os.getcwd(), "data", "uploads"), exist_ok=True)
app.mount("/public", StaticFiles(directory=os.path.join(database.os.getcwd(), "data", "public")), name="public")

@app.post("/jobs/", response_model=schemas.ScanJob)
async def create_job(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    video: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    if not video.filename.endswith(('.mp4', '.mov', '.avi')):
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    # Save the job in DB
    job = models.ScanJob(name=name, status=models.JobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Save video file
    video_path = os.path.join(database.os.getcwd(), "data", "uploads", f"{job.id}_{video.filename}")
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
        
    # Start background task
    background_tasks.add_task(processing.process_video_task, job.id, video_path)
    
    return job

@app.get("/jobs/", response_model=list[schemas.ScanJob])
def get_jobs(db: Session = Depends(database.get_db)):
    jobs = db.query(models.ScanJob).order_by(models.ScanJob.created_at.desc()).all()
    return jobs

@app.get("/jobs/{job_id}", response_model=schemas.ScanJob)
def get_job(job_id: int, db: Session = Depends(database.get_db)):
    job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(database.get_db)):
    job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up public assets if they exist
    public_folder = os.path.join(database.os.getcwd(), "data", "public", str(job.id))
    if os.path.exists(public_folder):
        shutil.rmtree(public_folder)
        
    db.delete(job)
    db.commit()
    return {"status": "ok"}
