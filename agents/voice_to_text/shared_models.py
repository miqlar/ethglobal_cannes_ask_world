"""
Shared models for agent-to-agent communication.
"""

from uagents import Model
from typing import Optional


class AudioTranscriptionRequest(Model):
    """Request model for audio transcription."""
    audio_data_base64: str  # Base64 encoded audio data
    mime_type: str
    source_blob_id: Optional[str] = None
    description: Optional[str] = None


class AudioTranscriptionResponse(Model):
    """Response model for audio transcription."""
    transcript: str
    success: bool
    error_message: Optional[str] = None
    source_blob_id: Optional[str] = None


class BlobDownloadRequest(Model):
    """Request model for blob download."""
    blob_id: str
    request_id: str


class BlobDownloadResponse(Model):
    """Response model for blob download."""
    blob_data_base64: str  # Base64 encoded blob data
    mime_type: str
    blob_id: str
    request_id: str
    success: bool
    error_message: Optional[str] = None 