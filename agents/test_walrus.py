#!/usr/bin/env python3
"""
Test script for walrus agent via REST endpoints.
"""

import asyncio
import base64
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

async def test_walrus_agent():
    """Test the walrus agent via REST endpoints."""
    
    print("🧪 Testing Walrus Agent REST Endpoints")
    print("=" * 50)
    
    # Test 1: Upload text
    print("\n1️⃣ Testing text upload...")
    text_payload = {
        "text": "Hello from the test script! This is a test text upload to Walrus.",
        "description": "Test text upload from REST endpoint"
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/upload-text",
            json=text_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Text upload successful!")
                print(f"📄 Blob ID: {result['blob_id']}")
                print(f"🔗 View at: {result['blob_url']}")
                
                # Store blob_id for download test
                test_blob_id = result['blob_id']
            else:
                print(f"❌ Text upload failed: {result.get('error_message')}")
                return
        else:
            print(f"❌ Text upload request failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed! Make sure the walrus agent is running on localhost:8001")
        print(f"💡 Start the agent with: cd walrus && python agent.py")
        return
    except Exception as e:
        print(f"❌ Text upload failed: {e}")
        return
    
    # Test 2: Download the blob we just uploaded
    print("\n2️⃣ Testing blob download...")
    download_payload = {
        "blob_id": test_blob_id,
        "request_id": "test-download-123"
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/download",
            json=download_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Blob download successful!")
                print(f"📄 Blob ID: {result['blob_id']}")
                print(f"📄 MIME type: {result['mime_type']}")
                print(f"📄 Data size: {len(result['blob_data_base64'])} base64 chars")
                
                # Decode and verify the data
                decoded_data = base64.b64decode(result['blob_data_base64'])
                print(f"📄 Decoded text: {decoded_data.decode('utf-8')}")
            else:
                print(f"❌ Blob download failed: {result.get('error_message')}")
        else:
            print(f"❌ Download request failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Blob download failed: {e}")
    
    # Test 3: Upload from URL
    print("\n3️⃣ Testing upload from URL...")
    url_payload = {
        "url": "https://ttsreader.com/images/avatars/adam.mp3",
        "description": "Test audio file upload from URL"
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/upload-url",
            json=url_payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for URL download
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ URL upload successful!")
                print(f"📄 Blob ID: {result['blob_id']}")
                print(f"🔗 View at: {result['blob_url']}")
                
                # Store audio blob_id for potential transcription test
                audio_blob_id = result['blob_id']
            else:
                print(f"❌ URL upload failed: {result.get('error_message')}")
        else:
            print(f"❌ URL upload request failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ URL upload failed: {e}")
    
    # Test 4: Upload binary data (if we have a test file)
    print("\n4️⃣ Testing binary data upload...")
    test_file_path = "../tests/adam.mp3"
    if os.path.exists(test_file_path):
        try:
            with open(test_file_path, 'rb') as f:
                file_data = f.read()
            
            binary_payload = {
                "data_base64": base64.b64encode(file_data).decode('utf-8'),
                "mime_type": "audio/mpeg",
                "description": "Test binary file upload from REST endpoint"
            }
            
            response = requests.post(
                "http://localhost:8001/upload",
                json=binary_payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Binary upload successful!")
                    print(f"📄 Blob ID: {result['blob_id']}")
                    print(f"🔗 View at: {result['blob_url']}")
                else:
                    print(f"❌ Binary upload failed: {result.get('error_message')}")
            else:
                print(f"❌ Binary upload request failed: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Binary upload failed: {e}")
    else:
        print(f"⏭️ Skipping binary upload test - test file not found: {test_file_path}")
    
    print("\n🎉 Walrus Agent REST endpoint tests completed!")

if __name__ == "__main__":
    asyncio.run(test_walrus_agent()) 