# Docker image for the application and tests
FROM python:3.12-slim

WORKDIR /app

# Install system deps if needed (none for this example)

# Install Python deps
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy app code and tests
COPY . .

# Default command runs the test suite
CMD ["pytest", "-q"]
