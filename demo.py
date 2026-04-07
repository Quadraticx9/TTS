import requests
import json
import time
from pydub import AudioSegment
import os
import re

# CONFIGURATION
API_URL = "http://127.0.0.1:8000/tts" # Replace with your URL
VOICE = "hi-IN-SwaraNeural" # Natural Hindi Female Voice
OUTPUT_FILE = "final_hindi_audio.mp3"
MAX_CHARS_PER_CHUNK = 350 # Safe limit to avoid timeouts/cuts

def split_text_into_chunks(text, max_chars):
    """
    Splits text into chunks by sentences to ensure natural pauses.
    """
    # Split by common Hindi/English sentence endings
    sentences = re.split(r'(?<=[.!?।\n])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def download_audio_chunk(text_chunk, index):
    """
    Downloads a single audio chunk from the Leapcell API.
    """
    print(f"Generating chunk {index + 1}: {text_chunk[:50]}...")
    
    params = {
        "text": text_chunk,
        "voice": VOICE,
        "rate": "+0%", # Adjust speed if needed, e.g., "+5%"
        "volume": "+0%"
    }
    
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            filename = f"chunk_{index}.mp3"
            with open(filename, "wb") as f:
                f.write(response.content)
            return filename
        else:
            print(f"Error generating chunk {index}: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed for chunk {index}: {e}")
        return None

def merge_audio_files(file_list, output_filename):
    """
    Merges multiple MP3 files into one.
    """
    if not file_list:
        print("No audio files to merge.")
        return

    combined = AudioSegment.empty()
    for file in file_list:
        if os.path.exists(file):
            audio = AudioSegment.from_mp3(file)
            combined += audio
            # Optional: Add a tiny silence between chunks for natural breath
            # combined += AudioSegment.silent(duration=100) 
            os.remove(file) # Clean up chunk file
        else:
            print(f"Warning: File {file} not found, skipping.")

    combined.export(output_filename, format="mp3")
    print(f"Success! Final audio saved as: {output_filename}")

def main():
    # Example Long Text (Hindi)
    long_text = """
    नमस्ते! यह एक स्वचालित ऑडियो जनरेशन परीक्षण है। 
    माइक्रोसॉफ्ट एज टीटीएस का उपयोग करके, हम बहुत ही प्राकृतिक और मानव जैसी आवाज़ें बना सकते हैं। 
    यह तकनीक वीडियो निर्माण, ऑडियोबुक और शिक्षण सामग्री के लिए बहुत उपयोगी है।
    हम इस स्क्रिप्ट का उपयोग करके लंबे टेक्स्ट को छोटे हिस्सों में बांटते हैं और फिर उन्हें जोड़ते हैं।
    इससे कोई भी त्रुटि नहीं होती और ऑडियो की गुणवत्ता बनी रहती है।
    आप इसका उपयोग अपने व्यापार या व्यक्तिगत परियोजनाओं के लिए कर सकते हैं।
    धन्यवाद!
    """

    print("Starting Audio Generation Process...")
    
    # 1. Split Text
    chunks = split_text_into_chunks(long_text, MAX_CHARS_PER_CHUNK)
    print(f"Text split into {len(chunks)} chunks.")
    
    # 2. Generate Audio for each chunk
    audio_files = []
    for i, chunk in enumerate(chunks):
        if not chunk: continue
        file_path = download_audio_chunk(chunk, i)
        if file_path:
            audio_files.append(file_path)
        time.sleep(0.5) # Polite delay to avoid rate limiting
        
    # 3. Merge Audio
    if audio_files:
        merge_audio_files(audio_files, OUTPUT_FILE)
    else:
        print("Failed to generate any audio.")

if __name__ == "__main__":
    main()