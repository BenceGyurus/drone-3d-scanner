import asyncio
import os
import shutil
import uuid
import ffmpeg
from pyodm import Node
from sqlalchemy.orm import Session
from . import models, database

NODE_URL = os.getenv("NODEODM_URL", "http://localhost:3000")
DATA_DIR = os.path.join(os.getcwd(), "data")

async def process_video_task(job_id: int, video_path: str):
    db: Session = database.SessionLocal()
    job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
    if not job:
        db.close()
        return

    job_folder = os.path.join(DATA_DIR, str(job.id))
    images_folder = os.path.join(job_folder, "images")
    os.makedirs(images_folder, exist_ok=True)

    try:
        # Step 1: Extract frames using FFmpeg
        job.status = models.JobStatus.EXTRACTING_FRAMES
        db.commit()
        
        # We extract 2 frames per second (can be tuned)
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

        # Step 2: Upload to NodeODM
        job.status = models.JobStatus.UPLOADING_TO_ODM
        db.commit()

        images = [os.path.join(images_folder, f) for f in os.listdir(images_folder) if f.endswith('.jpg')]
        if not images:
            raise Exception("No frames extracted from video.")

        node = Node.from_url(NODE_URL)
        task = node.create_task(images, {'auto-boundary': True, 'dsm': True, 'orthophoto-resolution': 5})
        
        job.odm_task_id = task.uuid
        job.status = models.JobStatus.PROCESSING_ODM
        db.commit()

        # Step 3: Poll NodeODM for completion
        task.wait_for_completion()

        # Step 4: Download Results
        job.status = models.JobStatus.DOWNLOADING_RESULTS
        db.commit()

        assets_folder = os.path.join(job_folder, "assets")
        os.makedirs(assets_folder, exist_ok=True)

        task.download_assets(assets_folder)

        # Look for the generated 3D model and orthophoto
        model_file = os.path.join(assets_folder, "odm_texturing", "odm_textured_model_geo.obj")
        if not os.path.exists(model_file):
            model_file = os.path.join(assets_folder, "odm_texturing", "odm_textured_model.obj")
        
        # We might need to copy these out so the static server can serve them easily
        public_folder = os.path.join(DATA_DIR, "public", str(job.id))
        os.makedirs(public_folder, exist_ok=True)
        
        if os.path.exists(model_file):
            shutil.copy(model_file, os.path.join(public_folder, "model.obj"))
            # Need the texture as well
            texture_file = os.path.join(os.path.dirname(model_file), "odm_textured_model_geo_material0000_map_Kd.png")
            if not os.path.exists(texture_file):
                texture_file = os.path.join(os.path.dirname(model_file), "odm_textured_model_material0000_map_Kd.png")
            if os.path.exists(texture_file):
                shutil.copy(texture_file, os.path.join(public_folder, "texture.png"))
            
            # Also the mtl file
            mtl_file = os.path.join(os.path.dirname(model_file), "odm_textured_model_geo.mtl")
            if not os.path.exists(mtl_file):
                mtl_file = os.path.join(os.path.dirname(model_file), "odm_textured_model.mtl")
            if os.path.exists(mtl_file):
                shutil.copy(mtl_file, os.path.join(public_folder, "model.mtl"))
            
            job.model_path = f"/public/{job.id}/model.obj"
            
        ortho_file = os.path.join(assets_folder, "odm_orthophoto", "odm_orthophoto.tif")
        if os.path.exists(ortho_file):
            shutil.copy(ortho_file, os.path.join(public_folder, "orthophoto.tif"))
            job.orthophoto_path = f"/public/{job.id}/orthophoto.tif"

        # Mocking GPS for demonstration on the map (OpenDroneMap outputs geo.json which could be parsed, 
        # but for this demo we'll center it on a default location with slight randomness).
        import random
        job.latitude = 47.4979 + (random.random() * 0.02 - 0.01)
        job.longitude = 19.0402 + (random.random() * 0.02 - 0.01)

        job.status = models.JobStatus.COMPLETED
        db.commit()

        # Step 5: Cleanup raw video and images
        try:
            os.remove(video_path)
            shutil.rmtree(images_folder)
            shutil.rmtree(assets_folder) # We copied the needed ones to public
            task.remove() # Clean up NodeODM node
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

    except Exception as e:
        job.status = models.JobStatus.FAILED
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
