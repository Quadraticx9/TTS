import os
import uuid
import time
from pathlib import Path
from config import settings

def generate_unique_filename(extension: str = "mp3") -> str:
    """Generate unique filename with timestamp"""
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:8]
    return f"tts_{timestamp}_{unique_id}.{extension}"

async def cleanup_old_files(directory: str, max_age_seconds: int):
    """Delete audio files older than max_age_seconds"""
    try:
        current_time = time.time()
        for file in Path(directory).glob(f"*.{settings.AUDIO_FORMAT}"):
            if current_time - file.stat().st_mtime > max_age_seconds:
                file.unlink(missing_ok=True)
    except Exception:
        pass  # Silent fail - don't break API on cleanup