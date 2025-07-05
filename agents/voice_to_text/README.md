# Voice-to-Text Agent

A uAgent that provides audio transcription services using OpenAI Whisper, with support for both chat interface and agent-to-agent communication.

## Features

- **Audio Transcription**: Transcribe audio files using OpenAI Whisper
- **Chat Interface**: Handle audio uploads through the chat protocol
- **Agent-to-Agent Communication**: Accept transcription requests from other agents
- **Multiple Audio Formats**: Support for MP3, WAV, M4A, FLAC, and more
- **Mailbox Mode**: Run in mailbox mode for persistent communication

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file in the parent directory (../.env) with:
OPENAI_API_KEY=your_openai_api_key_here

# Optional Whisper model (defaults to whisper-1)
export WHISPER_MODEL="whisper-1"
```

3. Run the agent:
```bash
python agent.py
```

## Platform Deployment

This agent is designed to be deployed independently on agent platforms. Each agent folder contains all necessary code and dependencies.

To deploy:
1. Upload the entire `voice_to_text/` folder to your agent platform
2. Set the required environment variables on the platform
3. The agent will automatically handle audio transcription requests

## Usage

### Chat Interface
- Attach audio files to transcribe them
- Send URLs to audio files for transcription
- Get immediate transcription results

### Agent-to-Agent Communication
The agent can receive transcription requests from other agents using the `AudioTranscriptionRequest` model:

```python
from shared_models import AudioTranscriptionRequest

request = AudioTranscriptionRequest(
    audio_data=audio_bytes,
    mime_type="audio/mp3",
    source_blob_id="blob_id_here",
    description="Optional description"
)
```

### Response Format
The agent responds with `AudioTranscriptionResponse`:

```python
from shared_models import AudioTranscriptionResponse

response = AudioTranscriptionResponse(
    transcript="Transcribed text here",
    success=True,
    source_blob_id="blob_id_here"
)
```

## Integration with Walrus Agent

This agent is designed to work seamlessly with the Walrus blob storage agent:

1. **Automatic Transcription**: When the Walrus agent downloads audio files, it automatically requests transcription
2. **Blob Tracking**: Transcription requests include source blob IDs for tracking
3. **Error Handling**: Comprehensive error handling and reporting
4. **Independent Deployment**: Each agent can be deployed separately on agent platforms

## Examples

### Chat Usage
- Attach an MP3 file → Get transcription
- Send URL: `https://example.com/audio.mp3` → Get transcription

### Agent Communication
- Walrus agent downloads audio blob → Automatically requests transcription
- Receives audio data → Returns transcribed text
- Handles errors gracefully with detailed error messages

## Configuration

The agent runs on port 8002 by default and uses mailbox mode for persistent communication. Make sure to note the agent's address when it starts up - other agents will need this address to send transcription requests. 