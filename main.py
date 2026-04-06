import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import scipy.io.wavfile as scipy_wav

app = FastAPI(title="Bark Small TTS API")

# Global variables to store the model and processor
model_id = "prince-canuma/bark-small"
processor = None
model = None
device = "cpu"  # Will be updated when model loads
is_ready = False

def get_model():
    global processor, model, is_ready, device
    if not is_ready:
        import torch
        from transformers import AutoProcessor, BarkModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading {model_id} on {device}...")
        processor = AutoProcessor.from_pretrained(model_id)
        model = BarkModel.from_pretrained(model_id).to(device)
        is_ready = True
        print("Model loaded successfully!")
    return processor, model, device

class TTSRequest(BaseModel):
    text: str
    voice_preset: str = "en_speaker_6"  

@app.post("/generate")
def generate_audio(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    try:
        import torch
        proc, mod, dev = get_model()
        
        inputs = proc(request.text, voice_preset=request.voice_preset).to(dev)
        with torch.no_grad():
            audio_array = mod.generate(**inputs)
        audio_array = audio_array.cpu().numpy().squeeze()
        sample_rate = mod.generation_config.sample_rate
        
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
