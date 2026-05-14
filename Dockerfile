# Use official high-performance Python slim image
FROM python:3.11-slim

# Set enterprise environment defaults
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONMENT production

WORKDIR /app

# Install system dependencies for reportlab and scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy clinical model
RUN python -m spacy download en_core_web_lg

# Copy application source
COPY . .

# Create storage directories for persistence
RUN mkdir -p storage/reports uploads/voice

# Expose port for Render/Vercel/K8s
EXPOSE 8000

# Start enterprise application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
