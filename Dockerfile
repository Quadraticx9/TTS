FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Tell Hugging Face to use /tmp as the cache directory since /app might be read-only in Leapcell
ENV HF_HOME="/tmp/huggingface"

# Pre-download the model at build time to make app startup drastically faster and prevent Leapcell timeout
RUN python -c "import os; os.environ['HF_HOME'] = '/tmp/huggingface'; from transformers import AutoProcessor, BarkModel; AutoProcessor.from_pretrained('prince-canuma/bark-small'); BarkModel.from_pretrained('prince-canuma/bark-small')"

RUN mkdir -p /tmp && chmod 777 /tmp

COPY main.py ./

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
