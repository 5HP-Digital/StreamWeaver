# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CONFIG_DIR=/config

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
  CMD curl -f http://localhost:8000/api/health/ || exit 1

# Run the application
WORKDIR /app
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "iptv_manager.asgi:application"]
