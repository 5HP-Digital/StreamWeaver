# Stage 1: Builder image
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies required for building
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Copy app
COPY . .

# Stage 2: Runtime image
FROM python:3.12-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CONFIG_DIR=/config
ENV USER=app

# Create app user for security
RUN groupadd -r app && useradd -r -M -g app ${USER}

# Set work directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy Python wheels from builder stage
COPY --from=builder /wheels /wheels

# Copy app from builder stage
COPY --from=builder /app .

# Install Python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Set proper permissions
RUN chown -R ${USER}:app /app && \
    mkdir -p ${CONFIG_DIR} && \
    chown -R ${USER}:app ${CONFIG_DIR}

# Stage 3: Web app image
FROM runtime AS final

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CONFIG_DIR=/config
ENV USER=app

WORKDIR /app

# Healthcheck
#HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
#  CMD curl -f http://localhost:8000/api/health/ || exit 1

# Switch to non-root user
USER ${USER}

# Run the application
CMD ["python", "manage.py", "qcluster"]
