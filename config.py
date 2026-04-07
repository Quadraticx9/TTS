import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Audio Settings
    MAX_TEXT_LENGTH: int = 5000  # ~60 seconds of speech
    OUTPUT_DIR: str = "/tmp/audio"  # Leapcell writable temp storage
    AUDIO_FORMAT: str = "mp3"
    SAMPLE_RATE: int = 24000
    
    # Edge TTS Voices (Microsoft Neural - Very Natural) [[33]][[34]]
    HINDI_VOICES = {
        "female": "hi-IN-SwaraNeural",    # ⭐ Best for YouTube narration
        "male": "hi-IN-MadhurNeural",     # Professional tutorials
        "expressive": "hi-IN-KavyaNeural" # Conversational content
    }
    
    ENGLISH_VOICES = {
        "female_in": "en-IN-NeerjaNeural",   # Indian English female
        "male_in": "en-IN-PrabhatNeural",    # Indian English male
        "female_us": "en-US-JennyNeural",    # US English (optional)
        "male_uk": "en-GB-RyanNeural"        # UK English (optional)
    }
    
    # Auto-cleanup (prevent storage bloat on Leapcell)
    CLEANUP_AFTER_SECONDS: int = 300  # Delete files after 5 minutes
    
    class Config:
        env_file = ".env"

settings = Settings()