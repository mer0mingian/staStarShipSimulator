# STA Starship Simulator - Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=sta.web.app:create_app \
    FLASK_ENV=production

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sta/ ./sta/

# Create directory for SQLite database (will be mounted as volume)
RUN mkdir -p /app/data

# Expose port (using 5001 to avoid macOS AirPlay conflict)
EXPOSE 5001

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "sta.web.app:create_app()"]
