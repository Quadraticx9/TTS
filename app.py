from fastapi import FastAPI
from pydantic import BaseModel
from TTS.api import TTS
import uuid
import os

app = FastAPI()

print("🔄 Loading XTTS model...")

# Load model once (IMPORTANT)
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

print("✅ Model loaded!")

# Request schema
class TTSRequest(BaseModel):
    text: str
    language: str = "en"

# Health check
@app.get("/")
def root():
    return {"status": "XTTS API is running"}

# Wake-up endpoint (for Make.com ping)
@app.get("/wake")
def wake():
    return {"message": "Server is awake"}

# Main TTS endpoint
@app.post("/tts")
def generate_tts(req: TTSRequest):
    try:
        file_name = f"{uuid.uuid4()}.wav"
        output_path = os.path.join("/tmp", file_name)

        tts.tts_to_file(
            text=req.text,
            file_path=output_path,
            language=req.language
        )

        return {
            "status": "success",
            "file": file_name
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}