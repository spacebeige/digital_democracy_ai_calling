# Multi-stage build for Meera Multilingual Grievance System
FROM python:3.12-slim as base

# Set environment to be non-interactive
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CUDA_VISIBLE_DEVICES="" \
    OMP_NUM_THREADS="1" \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core dependencies
    gcc \
    build-essential \
    # Audio support (optional - for microphone input)
    alsa-utils \
    portaudio19-dev \
    libportaudio2 \
    libsndfile1 \
    sox \
    # For TTS/Audio processing
    ffmpeg \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    # Database
    libpq-dev \
    # Utilities
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-db.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r requirements-db.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/outputs/json_results/{meera_interactions,by_urgency,by_department} && \
    mkdir -p /app/awaaz && \
    mkdir -p /tmp/recordings

# Expose ports
EXPOSE 8000 9000 9001 9002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run the main application
CMD ["python", "interactive_voice_to_layer3_integrated.py"]
