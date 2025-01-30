# Use Python 3.11.4 as base image
FROM python:3.11.4-slim

# Install system dependencies required for pdf2image and other packages
RUN apt-get update && apt-get install -y \
    poppler-utils \
    ffmpeg \
    libsndfile1 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a directory for storing history
RUN mkdir -p history

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/aoai_audio

# Expose the port the app runs on
EXPOSE 5001

# Add wait-for-it script to wait for database
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Command to run the application
CMD ["/wait-for-it.sh", "db:5432", "--", "python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5001"] 