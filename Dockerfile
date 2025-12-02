FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for building packages (keep if you need them)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY . /app

# Expose port
EXPOSE 5000

# Tell Flask how to create the app (factory pattern)
ENV FLASK_APP=app:create_app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV PYTHONUNBUFFERED=1

# Just run the Flask dev server
CMD ["flask", "run"]
