# Use Node.js with Chrome for Lighthouse
FROM node:20-slim

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean

# Install Lighthouse CLI
RUN npm install -g lighthouse

# Set working directory
WORKDIR /app

# Copy project files into container
COPY project/ .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose port for Render
EXPOSE 10000

# Run the Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
