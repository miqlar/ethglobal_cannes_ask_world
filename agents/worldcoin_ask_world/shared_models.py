"""
Shared models for simple blockchain agent.
"""

from uagents import Model


class FunctionCallRequest(Model):
    """Request model for function calls."""
    function_name: str


class FunctionCallResponse(Model):
    """Response model for function calls."""
    function_name: str
    result: str
    success: bool
    error_message: str = None


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
    error_message: str = None 