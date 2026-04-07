import edge_tts
import io
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional

app = FastAPI(title="Edge TTS API on Leapcell")

# Define some common voices for convenience
DEFAULT_VOICE = "en-US-GuyNeural"

@app.get("/")
def read_root():
    return {"message": "Edge TTS API is running. Use /tts endpoint."}

@app.get("/tts")
async def text_to_speech(
    text: str = Query(..., description="The text to convert to speech"),
    voice: Optional[str] = Query(DEFAULT_VOICE, description="The voice to use (e.g., en-US-GuyNeural)"),
    rate: Optional[str] = Query("+0%", description="Speech rate adjustment (e.g., +10%, -5%)"),
    volume: Optional[str] = Query("+0%", description="Volume adjustment (e.g., +10%, -5%)")
):
    """
    Generates speech from text using Microsoft Edge TTS.
    Returns an MP3 audio stream.
    """
    if not text:
        raise HTTPException(status_code=400, detail="Text parameter is required")

    try:
        # Initialize the Communicate object
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        
        # Create a buffer to store the audio data
        audio_buffer = io.BytesIO()
        
        # Stream the audio into the buffer
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        
        # Reset buffer position to the beginning
        audio_buffer.seek(0)
        
        # Return the audio as a streaming response
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech.mp3",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/voices")
async def list_voices():
    """
    Returns a list of available voices.
    Note: This might take a few seconds as it fetches from Microsoft.
    """
    try:
        voices = await edge_tts.list_voices()
        # Simplify the output to just name and short name
        simplified_voices = [
            {"name": v['ShortName'], "locale": v['Locale'], "gender": v['Gender']} 
            for v in voices
        ]
        return {"voices": simplified_voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching voices: {str(e)}")