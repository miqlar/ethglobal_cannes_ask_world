#!/usr/bin/env python3
"""
Test script for voice-to-text agent via REST endpoint.
"""

import asyncio
import base64
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

async def test_voice_to_text_agent():
    """Test the voice-to-text agent via REST endpoint."""
    
    # Check if we have a test audio file
    test_audio_path = "../tests/adam.mp3"
    if not os.path.exists(test_audio_path):
        print(f"❌ Test audio file not found: {test_audio_path}")
        print("Please ensure you have an audio file to test with.")
        return
    
    print(f"✅ Found test audio file: {test_audio_path}")
    
    # Read the audio file
    with open(test_audio_path, 'rb') as f:
        audio_data = f.read()
    
    print(f" Audio file size: {len(audio_data)} bytes")
    
    # Encode audio data as base64
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    # Create the request payload using the AudioTranscriptionRequest model
    request_payload = {
        "audio_data_base64": audio_base64,
        "mime_type": "audio/mpeg",
        "source_blob_id": "test_blob_123",
        "description": "Test audio file from test script"
    }
    
    print(f"🔗 Testing voice-to-text agent at http://localhost:8002/transcribe")
    print(f"📤 Sending transcription request...")
    
    try:
        # Make the HTTP POST request to the REST endpoint
        response = requests.post(
            "http://localhost:8002/transcribe",
            json=request_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f" Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Request successful!")
            print(f"📝 Response: {json.dumps(response_data, indent=2)}")
            
            # Extract the transcript from the response
            if response_data.get("success"):
                print(f"🎵 Transcription: {response_data['transcript']}")
            else:
                print(f"❌ Transcription failed: {response_data.get('error_message', 'Unknown error')}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed! Make sure the voice-to-text agent is running on localhost:8002")
        print(f"💡 Start the agent with: cd voice_to_text && python agent.py")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice_to_text_agent())