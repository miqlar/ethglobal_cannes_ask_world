"""
Transcribe one or more audio inputs with OpenAI Whisper.

Requirements
------------
pip install openai requests python-dotenv
# + uagents if you run the full agent
"""

import base64
import os
import tempfile
from typing import Any, List, Dict
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()                               # ← reads ../.env into env vars
client = OpenAI()                                    # uses OPENAI_API_KEY

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")


def _save_to_temp(data: bytes, suffix: str) -> str:
    """Write bytes to a temporary file and return the path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data)
    tmp.close()
    return tmp.name


def _transcribe_file(path: str) -> str:
    """Call Whisper on a local file."""
    with open(path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=f,
            response_format="text",
        )
    return resp.text if hasattr(resp, "text") else resp


def get_audio_transcription(content: List[Dict[str, Any]]) -> str:
    """
    Accepts ChatMessage `content` list and returns the combined transcript.
    Supports:
      • {"type": "resource", "mime_type": "audio/…", "contents": <base64>}
      • {"type": "text", "text": "https://example.com/file.mp3"}
    """
    transcripts = []

    for item in content:
        if item.get("type") == "resource" and item.get("mime_type", "").startswith("audio/"):
            audio_bytes = base64.b64decode(item["contents"])
            ext = "." + item["mime_type"].split("/")[-1]
            path = _save_to_temp(audio_bytes, ext)
            transcripts.append(_transcribe_file(path))
            os.remove(path)

        # ── URL pasted as plain text ─────────────────────────────────────────────
        elif item.get("type") == "text":
            # Clean up anything the chat UI tacked on (newlines, spaces, etc.).
            text = item["text"].strip()          # removes leading/trailing \r\n
            url  = text.split()[0]               # in case user pasted multiple words

            # Only continue if it really looks like a URL
            if url.startswith(("http://", "https://")):
                print(f"[audio-agent] Fetching audio from: {url}")  # ← debug output

                try:
                    with requests.get(url, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        # Infer an extension, default to .mp3
                        suffix = os.path.splitext(url)[-1] or ".mp3"
                        path   = _save_to_temp(r.content, suffix)
                except requests.exceptions.RequestException as exc:
                    transcripts.append(f"❌ Could not download audio → {exc}")
                    continue

                transcripts.append(_transcribe_file(path))
                os.remove(path)


    return "\n".join(transcripts) if transcripts else "No valid audio found."
