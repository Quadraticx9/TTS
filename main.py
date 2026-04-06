import os
import uuid
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

@app.on_event("startup")
def load_resources():
    global processor, model
    print(f"Loading {model_id} on {device}...")
    processor = AutoProcessor.from_pretrained(model_id)
    model = BarkModel.from_pretrained(model_id).to(device)
    print("Model loaded successfully!")

class TTSRequest(BaseModel):
    text: str
    voice_preset: str = "en_speaker_6"

@app.post("/generate")
def generate_audio(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    try:
        # Process the input text
        inputs = processor(request.text, voice_preset=request.voice_preset).to(device)
        
        # Generate audio
        with torch.no_grad():
            audio_array = model.generate(**inputs)
        
        # Convert to numpy array
        audio_array = audio_array.cpu().numpy().squeeze()
        
        # Get sample rate
        sample_rate = model.generation_config.sample_rate
        
        # Save audio to a temporary file
        filename = f"/tmp/{uuid.uuid4()}.wav"
        scipy_wav.write(filename, sample_rate, audio_array)
        
        # Return the generated audio file
        return FileResponse(
            path=filename, 
            media_type="audio/wav", 
            filename="output.wav"
        )
    except Exception as e:
        message = str(e)
        if "speaker_embeddings" in message and "does not exists" in message:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid voice_preset for this model. Try presets like 'en_speaker_6' "
                    "instead of 'v2/en_speaker_6'."
                ),
            )
        raise HTTPException(status_code=500, detail=message)

@app.get("/health")
def health():
    return {"status": "healthy", "device": device}
