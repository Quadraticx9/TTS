import edge_tts
import io
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
import re

app = FastAPI(title="Edge TTS API on Leapcell")

DEFAULT_VOICE = "en-US-GuyNeural"

# Regex patterns for validation (edge-tts strict formats)
RATE_PATTERN = r'^[+-]?\d+%$'  # e.g., "+10%", "-5%"
PITCH_PATTERN = r'^[+-]?\d+(\.\d+)?(Hz|st)$'  # e.g., "+5Hz", "-2.5st"
VOLUME_PATTERN = r'^[+-]?\d+%$'  # e.g., "+10%", "-5%" (NO dB support!)

@app.get("/")
def read_root():
    return {"message": "Edge TTS API is running. Use /tts endpoint."}

@app.get("/tts")
async def text_to_speech(
    text: str = Query(..., description="The text to convert to speech"),
    voice: str = Query(DEFAULT_VOICE, description="Voice name (e.g., en-US-GuyNeural, hi-IN-SwaraNeural)"),
    rate: str = Query("+0%", description="Speech rate. Format: '+10%', '-5%'. Range: -50% to +100%"),
    pitch: str = Query("+0Hz", description="Speech pitch. Format: '+5Hz', '-2st'. Range: -50Hz to +50Hz or semitones"),
    volume: str = Query("+0%", description="Volume. Format: '+10%', '-5%' ONLY. NO dB support. Range: -100% to +100%")
):
    """
    Generates speech from text using Microsoft Edge TTS with prosody control.
    Returns an MP3 audio stream.
    
    ⚠️ Parameter Formats (edge-tts strict):
    - rate: "+10%", "-5%" (percentage only)
    - pitch: "+5Hz", "-2st" (Hz or semitones)
    - volume: "+10%", "-5%" (percentage ONLY, NOT dB)
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text parameter is required and cannot be empty")

    # Validate parameter formats BEFORE calling edge-tts (better error messages)
    if not re.match(RATE_PATTERN, rate):
        raise HTTPException(status_code=400, detail=f"Invalid rate format '{rate}'. Use '+10%' or '-5%'")
    if not re.match(PITCH_PATTERN, pitch):
        raise HTTPException(status_code=400, detail=f"Invalid pitch format '{pitch}'. Use '+5Hz' or '-2st'")
    if not re.match(VOLUME_PATTERN, volume):
        raise HTTPException(status_code=400, detail=f"Invalid volume format '{volume}'. Use '+10%' or '-5%' (NO dB)")

    try:
        # Initialize the Communicate object with validated prosody controls
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        
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
                "Content-Disposition": "attachment; filename=speech.mp3",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Edge-TTS error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/voices")
async def list_voices():
    """Returns a list of available voices."""
    try:
        voices = await edge_tts.list_voices()
        simplified_voices = [
            {"name": v['ShortName'], "locale": v['Locale'], "gender": v['Gender']} 
            for v in voices
        ]
        return {"voices": simplified_voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching voices: {str(e)}")