#!/usr/bin/env python3
"""
Test script to demonstrate the walrus agent's clarification functionality.
"""

import asyncio
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

async def test_clarification():
    """Test the clarification functionality with unclear messages."""
    
    print("🧪 Testing Walrus Agent Clarification Functionality")
    print("=" * 60)
    
    # Test cases with unclear intent
    unclear_messages = [
        "I want to do something with files",
        "Can you help me?",
        "What can you do?",
        "I have some data",
        "Files are important",
        "Something about storage",
        "I need to save stuff"
    ]
    
    print("📝 Testing unclear messages that should trigger clarification...")
    print()
    
    for i, message in enumerate(unclear_messages, 1):
        print(f"{i}. Testing: '{message}'")
        
        # Create a simple text message payload
        payload = {
            "text": message
        }
        
        try:
            # Send to the upload-text endpoint (this will trigger intent detection)
            response = requests.post(
                "http://localhost:8001/upload-text",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"   ✅ Uploaded as text (intent was clear enough)")
                    print(f"   📄 Blob ID: {result['blob_id']}")
                else:
                    print(f"   ❌ Failed: {result.get('error_message')}")
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed! Make sure the walrus agent is running on localhost:8001")
            print(f"   💡 Start the agent with: cd walrus && python agent.py")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("🎯 Note: In the chat interface, unclear messages will trigger GPT-4 generated clarification messages!")
    print("💡 Try sending unclear messages like 'I want to do something with files' in the chat interface.")
    print("🤖 The agent will respond with helpful clarification using GPT-4!")

if __name__ == "__main__":
    asyncio.run(test_clarification()) 