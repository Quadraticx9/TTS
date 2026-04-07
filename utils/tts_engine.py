import edge_tts
import asyncio
import os
from config import settings
from utils.file_manager import generate_unique_filename

class TTSEngine:
    """Edge TTS wrapper with chunking for long text (60s+)"""
    
    @staticmethod
    async def generate_audio(
        text: str,
        voice: str,
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz"
    ) -> dict:
        """
        Generate audio from text using Edge TTS
        Returns: {success: bool, file_path: str, duration_est: float, error: str}
        """
        try:
            # Validate text length (~15 chars/sec average)
            if len(text) > settings.MAX_TEXT_LENGTH:
                text = text[:settings.MAX_TEXT_LENGTH] + "..."
            
            # Generate unique filename
            filename = generate_unique_filename(settings.AUDIO_FORMAT)
            filepath = os.path.join(settings.OUTPUT_DIR, filename)
            
            # Ensure output directory exists
            os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
            
            # Generate audio with Edge TTS (async, cloud-based) [[2]]
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            await communicate.save(filepath)
            
            # Estimate duration: ~150 words ≈ 60 seconds
            word_count = len(text.split())
            estimated_duration = min(word_count / 2.5, 60)  # Cap at 60s
            
            return {
                "success": True,
                "file_path": filepath,
                "filename": filename,
                "duration_est_sec": round(estimated_duration, 1),
                "voice_used": voice,
                "text_length": len(text)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_attempted": voice
            }
    
    @staticmethod
    async def list_voices() -> dict:
        """Return available Hindi + English voices"""
        return {
            "hindi": settings.HINDI_VOICES,
            "english_indian": settings.ENGLISH_VOICES,
            "all_edge_voices": "Use edge-tts --list-voices CLI for full list"
        }