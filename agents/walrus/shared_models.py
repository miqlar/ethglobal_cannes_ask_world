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


class BlobUploadRequest(Model):
    """Request model for blob upload."""
    data_base64: str  # Base64 encoded data
    mime_type: str
    description: Optional[str] = None


class BlobUploadResponse(Model):
    """Response model for blob upload."""
    blob_id: str
    blob_url: str
    success: bool
    error_message: Optional[str] = None


class BlobUploadFromUrlRequest(Model):
    """Request model for blob upload from URL."""
    url: str
    description: Optional[str] = None


class BlobUploadFromUrlResponse(Model):
    """Response model for blob upload from URL."""
    blob_id: str
    blob_url: str
    success: bool
    error_message: Optional[str] = None


class TextUploadRequest(Model):
    """Request model for text upload."""
    text: str
    description: Optional[str] = None


class TextUploadResponse(Model):
    """Response model for text upload."""
    blob_id: str
    blob_url: str
    success: bool
    error_message: Optional[str] = None


class BlobTranscriptionRequest(Model):
    """Request model for blob transcription."""
    blob_id: str
    request_id: str


class BlobTranscriptionResponse(Model):
    """Response model for blob transcription."""
    transcript: str
    blob_id: str
    request_id: str
    success: bool
    error_message: Optional[str] = None 