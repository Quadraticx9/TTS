import edge_tts
import io
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
import re
from typing import List

app = FastAPI(title="Edge TTS API on Leapcell")

DEFAULT_VOICE = "en-US-GuyNeural"

# Regex patterns for validation (edge-tts strict formats)
RATE_PATTERN = r'^[+-]?\d+%$'  # e.g., "+10%", "-5%"
PITCH_PATTERN = r'^[+-]?\d+(\.\d+)?(Hz|st)$'  # e.g., "+5Hz", "-2.5st"
VOLUME_PATTERN = r'^[+-]?\d+%$'  # e.g., "+10%", "-5%" (NO dB support!)


def speed_to_rate(speed: float) -> str:
    """Convert speed multiplier (e.g., 1.25x) to edge-tts rate format (e.g., +25%)."""
    rate_percent = round((speed - 1.0) * 100)
    sign = "+" if rate_percent >= 0 else ""
    return f"{sign}{rate_percent}%"


def normalize_text_for_natural_speech(text: str) -> str:
    """Normalize whitespace and line breaks so the model gets clearer prosody hints."""
    text = text.strip()
    # Keep paragraph separation while avoiding fragmented line-by-line speaking.
    text = re.sub(r"\n{2,}", "<PARA_BREAK>", text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace("<PARA_BREAK>", "\n\n")
    return text


def split_text_into_chunks(text: str, max_chunk_chars: int = 350) -> List[str]:
    """Split text into sentence-aware chunks for smoother long-form speech."""
    # Split on punctuation boundaries followed by whitespace.
    sentence_parts = re.split(r"(?<=[.!?])\s+", text)
    sentence_parts = [s.strip() for s in sentence_parts if s and s.strip()]

    if not sentence_parts:
        return []

    chunks: List[str] = []
    current = ""

    for sentence in sentence_parts:
        # Ensure each sentence has ending punctuation to improve cadence.
        if sentence[-1] not in ".!?":
            sentence += "."

        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_chunk_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks

@app.get("/")
def read_root():
    return {"message": "Edge TTS API is running. Use /tts endpoint."}

@app.get("/tts")
async def text_to_speech(
    text: str = Query(..., description="The text to convert to speech"),
    voice: str = Query(DEFAULT_VOICE, description="Voice name (e.g., en-US-GuyNeural, hi-IN-SwaraNeural)"),
    rate: str = Query("+0%", description="Speech rate. Format: '+10%', '-5%'. Range: -50% to +100%"),
    speed: float = Query(1.0, ge=0.5, le=2.0, description="Speed multiplier. Examples: 1.25, 1.5, 2.0. Overrides default rate when changed."),
    natural: bool = Query(True, description="Enable natural long-form speaking by sentence chunking and normalization"),
    max_chunk_chars: int = Query(350, ge=150, le=1200, description="Chunk size for long-form speech when natural=true"),
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

    # If speed is provided (not default), convert it to edge-tts rate format.
    # Prevent conflicting custom values when both speed and non-default rate are supplied.
    if speed != 1.0:
        if rate != "+0%":
            raise HTTPException(
                status_code=400,
                detail="Use either 'rate' or 'speed', not both at the same time"
            )
        rate = speed_to_rate(speed)

    # Validate parameter formats BEFORE calling edge-tts (better error messages)
    if not re.match(RATE_PATTERN, rate):
        raise HTTPException(status_code=400, detail=f"Invalid rate format '{rate}'. Use '+10%' or '-5%'")
    if not re.match(PITCH_PATTERN, pitch):
        raise HTTPException(status_code=400, detail=f"Invalid pitch format '{pitch}'. Use '+5Hz' or '-2st'")
    if not re.match(VOLUME_PATTERN, volume):
        raise HTTPException(status_code=400, detail=f"Invalid volume format '{volume}'. Use '+10%' or '-5%' (NO dB)")

    try:
        # Create a buffer to store the audio data
        audio_buffer = io.BytesIO()

        # Use sentence-aware chunking for long text to reduce robotic cadence.
        if natural:
            normalized_text = normalize_text_for_natural_speech(text)
            text_chunks = split_text_into_chunks(normalized_text, max_chunk_chars=max_chunk_chars)
        else:
            text_chunks = [text]

        if not text_chunks:
            raise HTTPException(status_code=400, detail="Text could not be parsed into valid chunks")

        # Stream each chunk sequentially into a single MP3 buffer.
        for chunk_text in text_chunks:
            communicate = edge_tts.Communicate(
                chunk_text,
                voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

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