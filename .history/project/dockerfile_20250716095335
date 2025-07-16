# Base image with Python
FROM python:3.10-slim

# Install dependencies for Node.js & Lighthouse
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g lighthouse \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Render
EXPOSE 8000

# Start app with Gunicorn (Render sets PORT env var)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
