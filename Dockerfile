# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code from retreat_app into /app
COPY retreat_app/ /app/

# Expose port (Flask runs on 5000 by default)
EXPOSE 5000

# Run the application directly
CMD ["python", "app.py"]
