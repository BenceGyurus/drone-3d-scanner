import asyncio
import os
import shutil
import subprocess
import ffmpeg
import random
from sqlalchemy.orm import Session
import models, database

DATA_DIR = os.path.join(os.getcwd(), "data")
# HOST_DATA_DIR is required so the backend knows where the data folder is mounted on the host machine.
# This is necessary because we are spawning a sibling Docker container that needs to mount the host path.
HOST_DATA_DIR = os.getenv("HOST_DATA_DIR", DATA_DIR)

async def process_video_task(job_id: int, video_path: str):
    db: Session = database.SessionLocal()
    job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
    if not job:
        db.close()
        return

    job_folder = os.path.join(DATA_DIR, str(job.id))
    images_folder = os.path.join(job_folder, "images")
    os.makedirs(images_folder, exist_ok=True)
    
    # Paths for host mounting
    host_job_folder = os.path.join(HOST_DATA_DIR, str(job.id))

    try:
        # Step 1: Extract frames using FFmpeg
        job.status = models.JobStatus.EXTRACTING_FRAMES
        db.commit()
        
        try:
            (
                ffmpeg
                .input(video_path)
                .filter('fps', fps=2)
                .output(os.path.join(images_folder, 'image_%04d.jpg'), **{'qscale:v': 2})
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            raise Exception(f"FFmpeg error: {e.stderr.decode('utf8')}")

        images = [f for f in os.listdir(images_folder) if f.endswith('.jpg')]
        if not images:
            raise Exception("No frames extracted from video.")

        # Step 2 & 3: Process with OpenDroneMap CLI via Docker
        job.status = models.JobStatus.PROCESSING_ODM
        db.commit()

        # We spawn the opendronemap/odm container. It will read from /datasets/{job_id}/images
        odm_cmd = [
            "docker", "run", "--rm",
            "-v", f"{HOST_DATA_DIR}:/datasets",
            "opendronemap/odm",
            "--project-path", "/datasets",
            str(job.id)
        ]
        
        # We can add parameters to speed up or improve results
        odm_cmd.extend(["--fast-orthophoto"])

        process = subprocess.run(odm_cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            raise Exception(f"ODM failed: {process.stderr}\n{process.stdout}")

        # Step 4: Collect Results
        job.status = models.JobStatus.DOWNLOADING_RESULTS
        db.commit()

        public_folder = os.path.join(DATA_DIR, "public", str(job.id))
        os.makedirs(public_folder, exist_ok=True)
        
        # Collect 3D Model
        model_file = os.path.join(job_folder, "odm_texturing", "odm_textured_model_geo.obj")
        if not os.path.exists(model_file):
            model_file = os.path.join(job_folder, "odm_texturing", "odm_textured_model.obj")
        
        if os.path.exists(model_file):
            shutil.copy(model_file, os.path.join(public_folder, "model.obj"))
            texture_file = os.path.join(os.path.dirname(model_file), "odm_textured_model_geo_material0000_map_Kd.png")
            if not os.path.exists(texture_file):
                texture_file = os.path.join(os.path.dirname(model_file), "odm_textured_model_material0000_map_Kd.png")
            if os.path.exists(texture_file):
                shutil.copy(texture_file, os.path.join(public_folder, "texture.png"))
            
            mtl_file = os.path.join(os.path.dirname(model_file), "odm_textured_model_geo.mtl")
            if not os.path.exists(mtl_file):
                mtl_file = os.path.join(os.path.dirname(model_file), "odm_textured_model.mtl")
            if os.path.exists(mtl_file):
                shutil.copy(mtl_file, os.path.join(public_folder, "model.mtl"))
            
            job.model_path = f"/public/{job.id}/model.obj"
            
        # Collect Orthophoto
        ortho_file = os.path.join(job_folder, "odm_orthophoto", "odm_orthophoto.tif")
        if os.path.exists(ortho_file):
            shutil.copy(ortho_file, os.path.join(public_folder, "orthophoto.tif"))
            job.orthophoto_path = f"/public/{job.id}/orthophoto.tif"

        # Mocking GPS for demonstration on the map
        job.latitude = 47.4979 + (random.random() * 0.02 - 0.01)
        job.longitude = 19.0402 + (random.random() * 0.02 - 0.01)

        job.status = models.JobStatus.COMPLETED
        db.commit()

        # Step 5: Cleanup raw video and processing files
        try:
            os.remove(video_path)
            # Remove the ODM output folders (keep the public copied assets)
            for item in os.listdir(job_folder):
                item_path = os.path.join(job_folder, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

    except Exception as e:
        job.status = models.JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
