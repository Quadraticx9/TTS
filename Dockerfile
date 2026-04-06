FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt huggingface_hub

# We copy the download script here and bake the model right into the Linux image
# This completely bypasses Github's 100MB file size limit for pushing models,
# while completely skipping the download locally
COPY download_model.py ./
RUN python download_model.py

# Now copy the app
COPY main.py ./

RUN mkdir -p /tmp && chmod 777 /tmp
ENV TMPDIR="/tmp"

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
