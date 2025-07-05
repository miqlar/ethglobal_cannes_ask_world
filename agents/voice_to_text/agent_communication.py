"""
Agent-to-agent communication protocol for the Audio-to-Text Agent.
"""

import base64
import tempfile
import os
from dotenv import load_dotenv
from uagents import Context, Protocol
from audio_analysis import get_audio_transcription

from shared_models import AudioTranscriptionRequest, AudioTranscriptionResponse

load_dotenv()

agent_comm_proto = Protocol()


@agent_comm_proto.on_message(model=AudioTranscriptionRequest)
async def handle_transcription_request(ctx: Context, sender: str, msg: AudioTranscriptionRequest):
    """Handle transcription requests from other agents."""
    ctx.logger.info(f"Received transcription request from {sender} for blob {msg.source_blob_id}")
    
    try:
        # Decode base64 audio data
        audio_data = base64.b64decode(msg.audio_data_base64)
        
        # Create a temporary file for the audio data
        suffix = "." + msg.mime_type.split("/")[-1] if "/" in msg.mime_type else ".audio"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(audio_data)
        tmp.close()
        
        # Transcribe the audio
        content = [{
            "type": "resource",
            "mime_type": msg.mime_type,
            "contents": msg.audio_data_base64  # Already base64 encoded
        }]
        
        transcript = get_audio_transcription(content)
        
        # Clean up temporary file
        os.remove(tmp.name)
        
        # Send success response
        response = AudioTranscriptionResponse(
            transcript=transcript,
            success=True,
            source_blob_id=msg.source_blob_id
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Transcription completed for blob {msg.source_blob_id}")
        
    except Exception as exc:
        ctx.logger.error(f"Transcription failed for blob {msg.source_blob_id}: {exc}")
        
        # Send error response
        response = AudioTranscriptionResponse(
            transcript="",
            success=False,
            error_message=str(exc),
            source_blob_id=msg.source_blob_id
        )
        
        await ctx.send(sender, response) 