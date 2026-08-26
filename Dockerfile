# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DB_NAME=/app/data/checklist.db

# Update system packages and clean cache to keep the image small
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code from retreat_app into /app
COPY retreat_app/ /app/

# Create directory for persistent SQLite database and declare it as a volume
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# Expose port (Flask runs on 5000 by default)
EXPOSE 5000

# Healthcheck to monitor application status (adapted from port 8000 to Flask's configured port 5000)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=5s \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/status')"

# Run the application using Gunicorn with real-time Docker logging and DEBUG level enabled
CMD ["sh", "-c", "python -c 'import app; app.init_db()' && gunicorn --bind 0.0.0.0:5000 --workers 2 --log-level debug --access-logfile - --error-logfile - --capture-output app:app"]
