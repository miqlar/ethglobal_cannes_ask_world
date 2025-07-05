# Walrus Blob Storage Agent

A uAgent that provides intelligent blob storage operations using the Walrus network with GPT-4-powered intent detection and smart clarification.

## Features

- **Advanced Intent Detection**: Uses GPT-4 to understand user intentions with high accuracy
- **Smart Clarification**: When intent is unclear, generates helpful clarification messages using GPT-4
- **Upload files**: Upload any file type to Walrus blob storage
- **Upload from URL**: Download and upload files from URLs
- **Upload text**: Store text data as blobs
- **Download blobs**: Download blobs using their blob ID
- **Natural Language**: Understand commands in natural language
- **Agent-to-Agent Communication**: Automatically transcribe audio files using the voice-to-text agent
- **REST API**: Direct HTTP endpoints for testing and integration

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file in the parent directory (../.env) with:
OPENAI_API_KEY=your_openai_api_key_here

# Optional Walrus configuration (uses defaults for testnet)
export WALRUS_PUBLISHER_URL="https://publisher.walrus-testnet.walrus.space"
export WALRUS_AGGREGATOR_URL="https://aggregator.walrus-testnet.walrus.space"
```

**Note**: For local development, the voice-to-text agent endpoint is automatically configured as `http://localhost:8002/transcribe`.

3. Run the agent:
```bash
python agent.py
```

## Platform Deployment

This agent is designed to be deployed independently on agent platforms. Each agent folder contains all necessary code and dependencies.

To deploy:
1. Upload the entire `walrus/` folder to your agent platform
2. Set the required environment variables on the platform
3. Configure the voice-to-text agent endpoint for the platform
4. The agent will automatically handle blob storage operations

## Usage

The agent uses advanced GPT-4 intent detection to understand your requests. When your intent is unclear, it will ask for clarification with helpful suggestions.

### Upload Operations

1. **Upload attached file**: Simply attach a file in the chat interface
2. **Upload from URL**: Send a URL starting with `http://` or `https://`
3. **Upload text**: Send any text message (will be stored as a blob)
4. **Natural language**: "Upload this file", "Store this text", "Save this URL"
5. **Explicit commands**: Use `/upload` followed by optional description

### Download Operations

1. **Download blob**: Use `/download <blob_id>` to download a specific blob
2. **Natural language**: "Download blob ABC123", "Get my file", "Retrieve the blob"

### Smart Clarification

When the agent can't clearly understand your intent, it will:
- Acknowledge your message
- Explain what it can help you with
- Ask specific questions to clarify your intent
- Provide examples of what you can do

## Examples

### Explicit Commands
- Upload a file: Attach any file to the chat
- Upload from URL: `https://example.com/file.mp3`
- Upload text: `Hello, this will be stored as a blob!`
- Download blob: `/download Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24`

### Natural Language
- "Upload this file for me"
- "Store this text message"
- "Download the blob with ID ABC123"
- "Save this URL to Walrus"
- "Help me with the available commands"

### Clarification Examples
- User: "I want to do something with files"
- Agent: "🤔 I'd be happy to help you with files! I can:
  • 📤 Upload files (attach them or send me URLs)
  • 📥 Download files (if you have a blob ID)
  • 📝 Store text as files
  
  Could you be more specific? For example:
  - 'Upload this file' (with attachment)
  - 'https://example.com/file.mp3' (upload from URL)
  - '/download ABC123' (download a blob)"

### Agent-to-Agent Features
- **Automatic Audio Transcription**: When downloading audio files (MP3, WAV, etc.), the agent automatically requests transcription from the voice-to-text agent
- **Seamless Integration**: Works with the voice-to-text agent for complete audio processing workflows
- **Independent Deployment**: Each agent can be deployed separately on agent platforms

## REST API Endpoints

For testing and direct integration, the agent provides REST endpoints:

- `POST /upload` - Upload binary data (base64 encoded)
- `POST /upload-url` - Upload file from URL
- `POST /upload-text` - Upload text as a blob
- `POST /download` - Download blob by ID

See `test_walrus.py` for examples of how to use these endpoints.

## Response Format

Successful uploads return:
```
✅ File uploaded successfully!
Blob ID: Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24
View at: https://walruscan.com/testnet/blob/Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24
```

Successful downloads return:
```
✅ Blob downloaded successfully!
Blob ID: Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24
File size: 453312 bytes
🎵 Audio file detected! (MIME: audio/mpeg) Requesting transcription...
📝 Transcription: Hello, this is a test audio file...
``` 