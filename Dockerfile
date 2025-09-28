# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  postgresql-client \
  curl \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Create necessary directories, users, and log files
RUN mkdir -p staticfiles media logs \
  && useradd -m -u 1000 appuser \
  && chown -R appuser:appuser /app \
  && ls -la /app/logs

# Collect static files as root (safe, no logging yet)
RUN python manage.py collectstatic --noinput --settings=job_platform.settings

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "job_platform.wsgi:application"]
