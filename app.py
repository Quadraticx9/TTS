from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import os
from config import settings
from utils.tts_engine import TTSEngine
from utils.file_manager import cleanup_old_files

app = FastAPI(
    title="Edge TTS YouTube API",
    description="Generate natural Hindi/English audio for YouTube automation",
    version="1.0.0"
)

# Request Models
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert (max ~60s speech)")
    language: str = Field(default="hindi", pattern="^(hindi|english)$", description="Language preference")
    voice_type: str = Field(default="female", pattern="^(female|male|expressive)$", description="Voice style")
    rate: str = Field(default="+0%", pattern="^[-+]?\\d+%$", description="Speech rate adjustment")
    volume: str = Field(default="+0%", pattern="^[-+]?\\d+%$", description="Volume adjustment")

@app.on_event("startup")
async def startup_event():
    """Ensure output directory exists"""
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {
        "service": "Edge TTS YouTube API",
        "status": "online",
        "docs": "/docs",
        "supported_languages": ["hindi", "english"],
        "max_duration": "60 seconds",
        "ram_usage": "<150MB"
    }

@app.get("/voices")
async def get_voices():
    """List available voices for YouTube content"""
    return await TTSEngine.list_voices()

@app.post("/generate")
async def generate_tts(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Generate audio file from text
    Returns download URL + metadata
    """
    # Select voice based on language + type
    if request.language == "hindi":
        voice = settings.HINDI_VOICES.get(request.voice_type, settings.HINDI_VOICES["female"])
    else:
        voice = settings.ENGLISH_VOICES.get(f"{request.voice_type}_in", settings.ENGLISH_VOICES["female_in"])
    
    # Generate audio
    result = await TTSEngine.generate_audio(
        text=request.text,
        voice=voice,
        rate=request.rate,
        volume=request.volume
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Schedule cleanup after delivery
    background_tasks.add_task(
        cleanup_old_files, 
        settings.OUTPUT_DIR, 
        settings.CLEANUP_AFTER_SECONDS
    )
    
    # Return download info
    download_url = f"/download/{result['filename']}"
    return {
        "success": True,
        "download_url": download_url,
        "filename": result["filename"],
        "estimated_duration_sec": result["duration_est_sec"],
        "voice_used": result["voice_used"],
        "text_processed_chars": result["text_length"],
        "expires_in_seconds": settings.CLEANUP_AFTER_SECONDS
    }

@app.get("/download/{filename}")
async def download_audio(filename: str):
    """Serve generated audio file"""
    filepath = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file expired or not found")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type=f"audio/{settings.AUDIO_FORMAT}"
    )

@app.get("/health")
async def health_check():
    """Health endpoint for Leapcell monitoring"""
    return {"status": "healthy", "ram_limit": "4GB", "tts_service": "edge-tts"}