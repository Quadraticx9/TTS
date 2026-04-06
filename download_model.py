import os
from huggingface_hub import snapshot_download

model_id = "suno/bark-small" # Switching to suno/bark-small which has all language presets (hi, en, etc)
local_dir = "/app/model"

print(f"Downloading {model_id} to {local_dir}...")
snapshot_download(
    repo_id=model_id,
    local_dir=local_dir,
    # We only need safetensors. Ignoring heavy .bin files saves space and memory
    ignore_patterns=["*.bin", "*.pt", "*.msgpack", "*.h5"] 
)
print("Download complete!")
