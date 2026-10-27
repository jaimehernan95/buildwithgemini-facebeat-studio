FROM python:3.12-slim

WORKDIR /app

# Install system utilities & multimedia libraries (FFmpeg for 9:16 clip exports, libsndfile1 for audio synthesis)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure storage directories exist
RUN mkdir -p /app/data /app/app/static/media/clips /app/app/static/audio

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

# Dynamic port execution for Cloud Run compatibility
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
