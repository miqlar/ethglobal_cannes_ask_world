"""
Audio-to-Text uAgent entrypoint.
"""

from uagents import Agent
from chat_proto import chat_proto
from agent_communication import agent_comm_proto
from shared_models import AudioTranscriptionRequest, AudioTranscriptionResponse

# Configure agent for mailbox mode
SEED_PHRASE = "put_your_seed_phrase_here"

agent = Agent(
    name="voice-to-text",
    port=8002,  # Using 8002 to avoid conflicts with other agents
    #endpoint=["http://localhost:8002/submit"],
    mailbox=False
)

# Include chat protocol and publish manifest so ASI:One / Agentverse can find it
agent.include(chat_proto, publish_manifest=True)

# Include agent communication protocol
agent.include(agent_comm_proto)

# Add REST endpoint for direct transcription testing
@agent.on_rest_post("/transcribe", AudioTranscriptionRequest, AudioTranscriptionResponse)
async def handle_transcription_rest(ctx, req: AudioTranscriptionRequest) -> AudioTranscriptionResponse:
    """REST endpoint for audio transcription."""
    ctx.logger.info(f"Received REST transcription request for blob {req.source_blob_id}")
    
    try:
        # Import the transcription function
        from audio_analysis import get_audio_transcription
        
        # Create content in the format expected by get_audio_transcription
        content = [{
            "type": "resource",
            "mime_type": req.mime_type,
            "contents": req.audio_data_base64
        }]
        
        # Transcribe the audio
        transcript = get_audio_transcription(content)
        
        # Return success response
        return AudioTranscriptionResponse(
            transcript=transcript,
            success=True,
            source_blob_id=req.source_blob_id
        )
        
    except Exception as exc:
        ctx.logger.error(f"Transcription failed for blob {req.source_blob_id}: {exc}")
        
        # Return error response
        return AudioTranscriptionResponse(
            transcript="",
            success=False,
            error_message=str(exc),
            source_blob_id=req.source_blob_id
        )

# Copy the address shown below
print(f"Your agent's address is: {agent.address}")

if __name__ == "__main__":
    agent.run()
