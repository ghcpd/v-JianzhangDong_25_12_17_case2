FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y zip && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY input.py .
COPY input_backup.py .

# Create configs and logs directories
RUN mkdir -p configs logs

# Expose port
EXPOSE 5000

# Set environment variables for security
ENV FLASK_DEBUG=False
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/')" || exit 1

# Run the application
CMD ["python", "input.py"]
