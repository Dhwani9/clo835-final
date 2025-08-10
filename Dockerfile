# Dockerfile
FROM python:3.11-slim

# Keep SSL certs current (helps with S3/TLS)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies (layered for caching)
COPY flask_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY flask_app/ ./flask_app/

# Move into the app dir
WORKDIR /app/flask_app

# Expose assignment port (the app default is 81)
EXPOSE 81

# Run the Flask app
CMD ["python", "app.py"]

