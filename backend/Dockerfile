# ==============================================================================
# LegalEase AI - Production Backend Container
# Multi-stage image with Tesseract OCR (Eng/Hin) & PyMuPDF graphics dependencies
# ==============================================================================

FROM python:3.11-slim-bookworm

# Install system packages required for Tesseract OCR and PyMuPDF (fitz)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specification and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code into container
COPY . .

# Ensure storage and ChromaDB directories exist
RUN mkdir -p /app/storage/uploads /app/storage/drafts /app/chroma_data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

# Start Uvicorn binding to 0.0.0.0 and honoring Render's dynamic $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
