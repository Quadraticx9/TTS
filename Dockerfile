# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary system dependencies for audio processing if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model to save time during runtime
RUN python -c "from transformers import AutoProcessor, BarkModel; model_id='prince-canuma/bark-small'; AutoProcessor.from_pretrained(model_id); BarkModel.from_pretrained(model_id)"

# Create a /tmp directory for saving temporary audio files
RUN mkdir -p /tmp && chmod 777 /tmp

# Copy the current directory contents into the container at /app
COPY main.py ./

# Expose port (Leapcell usually handles port allocation, but 8080 is a good default)
EXPOSE 8080

# Run FastAPI using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
