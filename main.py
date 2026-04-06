import os
os.environ["TMPDIR"] = "/tmp"

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import torch
from transformers import AutoProcessor, BarkModel
import scipy.io.wavfile as scipy_wav

app = FastAPI(title="Bark Small TTS API")

# We point directly to the folder we downloaded during Docker build
model_path = "/app/model"
processor = None
model = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def load_model():
    global processor, model
    # We lazy-load the model when the FIRST request hits
    # This guarantees the server binds port 8080 instantly and passes Leapcell's 9s health check!
    if model is None:
        print(f"Loading {model_path} into RAM on {device}...")
        processor = AutoProcessor.from_pretrained(model_path)
        model = BarkModel.from_pretrained(model_path).to(device)
        print("Model loaded successfully!")

class TTSRequest(BaseModel):
    text: str
    voice_preset: str = "v2/en_speaker_6"  

@app.post("/generate")
def generate_audio(request: TTSRequest):
    try:
        # Takes ~4 seconds ONLY on the very first request
        load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model from disk: {str(e)}")
        
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    try:
        inputs = processor(request.text, voice_preset=request.voice_preset).to(device)
        with torch.no_grad():
            audio_array = model.generate(**inputs)
        audio_array = audio_array.cpu().numpy().squeeze()
        sample_rate = model.generation_config.sample_rate
        
        filename = f"/tmp/{uuid.uuid4()}.wav"
        scipy_wav.write(filename, sample_rate, audio_array)
        
        return FileResponse(path=filename, media_type="audio/wav", filename="output.wav")
    except Exception as e:
        message = str(e)
        if "speaker_embeddings" in message:
            # Helpful error if voice preset uses wrong format
            raise HTTPException(status_code=400, detail=f"Invalid voice_preset format. Error: {message}")
        raise HTTPException(status_code=500, detail=message)

@app.get("/")
@app.get("/health")
@app.get("/kaithheathcheck")
def health():
    # If the model variable is populated, ready is True.
    # Otherwise False, until the first /generate request.
    return {"status": "healthy", "ready": model is not None, "device": device}
