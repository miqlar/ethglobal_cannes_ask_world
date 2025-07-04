"""
pip install --upgrade openai requests
export OPENAI_API_KEY="sk-..."   # or set another way
"""

import os
import tempfile
import requests
from openai import OpenAI

client = OpenAI()                       # uses OPENAI_API_KEY from env

def transcribe_from_url(audio_url: str) -> str:
    """
    Fetch an audio file at `audio_url`, run it through Whisper,
    and return the plain-text transcription.
    """
    # 1) Download to a temporary file
    with requests.get(audio_url, stream=True, timeout=30) as resp:
        resp.raise_for_status()
        suffix = os.path.splitext(audio_url)[-1] or ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in resp.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name                     # keep name after close

    # 2) Ask Whisper to transcribe
    with open(tmp_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",      # or "whisper-1-zh", etc.
            file=f,
            response_format="text"  # "srt" / "vtt" / "verbose_json" also possible
        )

    # 3) Clean up and return
    os.remove(tmp_path)
    return transcript.text if hasattr(transcript, "text") else transcript  # SDK ≥1.14

# ---- example usage ----
if __name__ == "__main__":
    url = "https://cdn.example.com/podcast/episode45.mp3"
    print(transcribe_from_url(url))
