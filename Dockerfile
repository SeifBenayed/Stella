# Use latest stable slim image
FROM python:3.9-slim

# Install system dependencies and Firefox
RUN apt-get update && apt-get install -y \
    curl \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install fastapi uvicorn[standard] Pillow

# Install Playwright with Firefox
RUN pip install playwright && \
    playwright install firefox && \
    playwright install-deps

# Create tmp_folder
RUN mkdir -p /app/tmp_folder

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV tmp_folder=/app/tmp_folder

# Expose the port for FastAPI
EXPOSE 8080

# Start the FastAPI server
CMD ["python", "hemden.py",  "--host", "0.0.0.0", "--timeout-keep-alive" ,"0", "--port", "80"]