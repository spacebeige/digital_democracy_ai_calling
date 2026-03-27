FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for audio processing/PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libvqf-dev \
    libsndfile1 \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt requirements-db.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-db.txt

# Copy the actual application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
