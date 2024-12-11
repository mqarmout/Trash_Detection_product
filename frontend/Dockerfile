
# Use an official Python 3.8 base image
FROM python:3.10-slim

# Install system dependencies (for OpenCV, PyTorch, etc.)
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    build-essential \
    libopenblas-dev \
    libomp-dev \
    libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app.py and other necessary files (like HTML)
COPY . .

# Expose the port your Flask app runs on
ENTRYPOINT ["python"]
# Command to run the Flask application
CMD ["app.py"]
