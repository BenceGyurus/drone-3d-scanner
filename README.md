# drone-3d-scanner

A modern, minimalist web application to extract frames from drone videos, process them with OpenDroneMap (ODM), and visualize the resulting 3D models in an interactive browser viewer.

## Features

- **Video Upload**: Upload drone videos directly in the browser. The backend automatically extracts frames using FFmpeg.
- **OpenDroneMap Integration**: Feeds extracted frames into NodeODM for photogrammetry processing.
- **3D Viewer**: Interactively view the generated 3D models (OBJ/GLB) directly in the browser.
- **Library**: Keep track of past scans, their statuses, and download previous results.

## Quick Start (with Docker Compose)

The easiest way to run the application is using the pre-built images from GitHub Container Registry (GHCR) along with the official OpenDroneMap NodeODM image.

```bash
docker-compose up -d
```

Once started, the application will be available at:
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000

The backend natively orchestrates the `opendronemap/odm` Docker container dynamically as needed using Docker socket mounting.

### GPU Support

To run ODM with GPU support for significantly faster processing, you can edit `backend/processing.py` to change the `opendronemap/odm` image string to `opendronemap/odm:gpu`, and pass the `--gpus all` flags to the subprocess arguments. You must have the NVIDIA Container Toolkit installed on your Linux host.

## Development

### Backend (Python/FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest test_main.py
uvicorn main:app --reload
```

### Frontend (React/Vite)

```bash
cd frontend
npm install
npm run dev
```
