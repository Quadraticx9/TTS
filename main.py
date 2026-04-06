import os
import uuid
import threading
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import torch
from transformers import AutoProcessor, BarkModel
import scipy.io.wavfile as scipy_wav

app = FastAPI(title="Bark Small TTS API")

# Global variables to store the model and processor
model_id = "prince-canuma/bark-small"
processor = None
model = None
device = "cuda" if torch.cuda.is_available() else "cpu"
is_ready = False

def load_model_bg():
    global processor, model, is_ready
    print(f"Loading {model_id} on {device}...")
    try:
        processor = AutoProcessor.from_pretrained(model_id)
        model = BarkModel.from_pretrained(model_id).to(device)
        is_ready = True
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")

@app.on_event("startup")
def load_resources():
    # Load in background so the port binds immediately and Leapcell health checks pass
    threading.Thread(target=load_model_bg, daemon=True).start()

class TTSRequest(BaseModel):
    text: str
    voice_preset: str = "en_speaker_6"  

@app.post("/generate")
def generate_audio(request: TTSRequest):
    if not is_ready:
        raise HTTPException(status_code=503, detail="Model is still downloading/loading on the server. Please try again in 30-60 seconds.")
        
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
        if "speaker_embeddings" in message and "does not exists" in message:
            raise HTTPException(status_code=400, detail="Invalid voice_preset for this model. Try presets like 'en_speaker_6' or 'hi_speaker_0'.")
        raise HTTPException(status_code=500, detail=message)

@app.get("/")
@app.get("/health")
@app.get("/kaithheathcheck")
def health():
    return {"status": "healthy", "ready": is_ready, "device": device}
