# SoloNest Production Dockerfile for Google Cloud Run
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Collect static files for WhiteNoise
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# Execute migrations and launch Gunicorn on Cloud Run
CMD python manage.py migrate --noinput && gunicorn soloNest.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --log-file -
