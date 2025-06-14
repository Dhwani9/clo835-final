FROM python:3.8-slim

WORKDIR /app

# Copy code and templates
COPY . /app
COPY templates/ /app/templates/

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variable for Flask (optional if using app.py directly)
ENV FLASK_APP=app.py

# Run the app directly with Python instead of Flask CLI
CMD ["python3", "app.py"]
