FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg and Docker CLI
RUN apt-get update && apt-get install -y ffmpeg docker.io && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
