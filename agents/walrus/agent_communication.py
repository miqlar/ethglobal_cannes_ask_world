"""
Agent-to-agent communication protocol for the Walrus Agent.
"""

import os
import requests
from uagents import Context, Protocol
from walrus_operations import _download_blob_data

from shared_models import BlobDownloadRequest, BlobDownloadResponse, AudioTranscriptionRequest, AudioTranscriptionResponse

# Import config to get the agent address
try:
    from config import VOICE_TO_TEXT_AGENT_ADDRESS
except ImportError:
    # Fallback to environment variable if config import fails
    VOICE_TO_TEXT_AGENT_ADDRESS = os.getenv("VOICE_TO_TEXT_AGENT_ADDRESS", "http://localhost:8002/transcribe")

agent_comm_proto = Protocol()

# Debug logging
print(f"🔗 Voice-to-text agent configured: {VOICE_TO_TEXT_AGENT_ADDRESS}")


def is_localhost_address(address: str) -> bool:
    """Check if the address is a localhost REST endpoint."""
    return address.startswith(("http://localhost", "http://127.0.0.1")) or "localhost" in address


@agent_comm_proto.on_message(model=BlobDownloadRequest)
async def handle_blob_download_request(ctx: Context, sender: str, msg: BlobDownloadRequest):
    """Handle blob download requests from other agents."""
    ctx.logger.info(f"Received blob download request from {sender} for blob {msg.blob_id}")
    
    try:
        # Download the blob data
        blob_data, mime_type = _download_blob_data(msg.blob_id)
        
        # Encode blob data as base64
        import base64
        blob_data_base64 = base64.b64encode(blob_data).decode('utf-8')
        
        # Send success response
        response = BlobDownloadResponse(
            blob_data_base64=blob_data_base64,
            mime_type=mime_type,
            blob_id=msg.blob_id,
            request_id=msg.request_id,
            success=True
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Blob download completed for {msg.blob_id}")
        
    except Exception as exc:
        ctx.logger.error(f"Blob download failed for {msg.blob_id}: {exc}")
        
        # Send error response
        response = BlobDownloadResponse(
            blob_data_base64="",
            mime_type="",
            blob_id=msg.blob_id,
            request_id=msg.request_id,
            success=False,
            error_message=str(exc)
        )
        
        await ctx.send(sender, response)


@agent_comm_proto.on_message(model=AudioTranscriptionResponse)
async def handle_transcription_response(ctx: Context, sender: str, msg: AudioTranscriptionResponse):
    """Handle transcription responses from the voice-to-text agent."""
    ctx.logger.info(f"Received transcription response from {sender} for blob {msg.source_blob_id}")
    
    if msg.success:
        ctx.logger.info(f"Transcription successful: {msg.transcript[:100]}...")
        # You could store this result or forward it to the original user
    else:
        ctx.logger.error(f"Transcription failed: {msg.error_message}")


async def request_audio_transcription(ctx: Context, audio_data: bytes, mime_type: str, blob_id: str, description: str = None):
    """Request audio transcription from the voice-to-text agent."""
    
    # Check if we're using localhost (REST) or remote agent (agent-to-agent)
    if is_localhost_address(VOICE_TO_TEXT_AGENT_ADDRESS):
        return await _request_transcription_via_rest(ctx, audio_data, mime_type, blob_id, description)
    else:
        return await _request_transcription_via_agent(ctx, audio_data, mime_type, blob_id, description)


async def _request_transcription_via_rest(ctx: Context, audio_data: bytes, mime_type: str, blob_id: str, description: str = None):
    """Request audio transcription via REST endpoint (for localhost)."""
    try:
        # Encode audio data as base64
        import base64
        audio_data_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Create the request payload
        request_payload = {
            "audio_data_base64": audio_data_base64,
            "mime_type": mime_type,
            "source_blob_id": blob_id,
            "description": description
        }
        
        ctx.logger.info(f"Sending transcription request to voice-to-text agent REST endpoint for blob {blob_id}")
        
        # Make HTTP POST request to the REST endpoint
        response = requests.post(
            VOICE_TO_TEXT_AGENT_ADDRESS,
            json=request_payload,
            headers={"Content-Type": "application/json"},
            timeout=60.0
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get("success"):
                transcript = response_data.get("transcript", "")
                ctx.logger.info(f"Transcription completed for blob {blob_id}")
                return f"\n📝 Transcription: {transcript}"
            else:
                error_message = response_data.get("error_message", "Unknown error")
                ctx.logger.error(f"Transcription failed for blob {blob_id}: {error_message}")
                return f"\n❌ Transcription failed: {error_message}"
        else:
            ctx.logger.error(f"Transcription request failed with status {response.status_code}: {response.text}")
            return f"\n❌ Transcription request failed: HTTP {response.status_code}"
        
    except requests.exceptions.ConnectionError:
        ctx.logger.error(f"Connection failed to voice-to-text agent at {VOICE_TO_TEXT_AGENT_ADDRESS}")
        return f"\n❌ Transcription request failed: Connection error - make sure voice-to-text agent is running"
    except Exception as exc:
        ctx.logger.error(f"Failed to send transcription request: {exc}")
        return f"\n❌ Transcription request failed: {exc}"


async def _request_transcription_via_agent(ctx: Context, audio_data: bytes, mime_type: str, blob_id: str, description: str = None):
    """Request audio transcription via agent-to-agent communication (for remote agents)."""
    try:
        # Encode audio data as base64
        import base64
        audio_data_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Create the transcription request
        request = AudioTranscriptionRequest(
            audio_data_base64=audio_data_base64,
            mime_type=mime_type,
            source_blob_id=blob_id,
            description=description
        )
        
        ctx.logger.info(f"Sending transcription request to voice-to-text agent {VOICE_TO_TEXT_AGENT_ADDRESS} for blob {blob_id}")
        
        # Send request and wait for response
        response, status = await ctx.send_and_receive(
            VOICE_TO_TEXT_AGENT_ADDRESS, 
            request, 
            response_type=AudioTranscriptionResponse
        )
        
        if isinstance(response, AudioTranscriptionResponse):
            if response.success:
                ctx.logger.info(f"Transcription completed for blob {blob_id}")
                return f"\n📝 Transcription: {response.transcript}"
            else:
                error_message = response.error_message or "Unknown error"
                ctx.logger.error(f"Transcription failed for blob {blob_id}: {error_message}")
                return f"\n❌ Transcription failed: {error_message}"
        else:
            ctx.logger.error(f"Failed to receive response from voice-to-text agent: {status}")
            return f"\n❌ Transcription request failed: {status}"
        
    except Exception as exc:
        ctx.logger.error(f"Failed to send transcription request to agent: {exc}")
        return f"\n❌ Transcription request failed: {exc}" 