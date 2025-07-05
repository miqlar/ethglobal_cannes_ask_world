"""
Intent detection for Walrus Blob Storage Agent using OpenAI.

Requirements
------------
pip install openai python-dotenv
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

# Intent categories
INTENTS = {
    "upload_file": "User wants to upload a file (attached or from URL)",
    "upload_text": "User wants to upload text content as a blob",
    "download_blob": "User wants to download a blob using its ID",
    "list_blobs": "User wants to list their blobs or get blob information",
    "help": "User needs help or wants to see available commands",
    "unknown": "User's intent is unclear or not supported"
}

# System prompt for intent classification
INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a Walrus blob storage agent. Analyze the user's message and determine their intent.

Available intents:
- upload_file: User wants to upload a file (attached or from URL)
- upload_text: User wants to upload text content as a blob
- download_blob: User wants to download a blob using its ID
- list_blobs: User wants to list their blobs or get blob information
- help: User needs help or wants to see available commands
- unknown: User's intent is unclear or not supported

Return a JSON object with:
{
    "intent": "intent_name",
    "confidence": 0.95,
    "extracted_data": {
        "blob_id": "extracted_blob_id_if_any",
        "url": "extracted_url_if_any",
        "description": "any_description_provided"
    }
}

Be more strict with confidence scores. Only give high confidence (>0.8) when the intent is very clear.
"""

# System prompt for generating clarification messages
CLARIFICATION_SYSTEM_PROMPT = """
You are a helpful Walrus blob storage agent assistant. The user's message is unclear, and you need to ask for clarification.

Available operations:
- Upload files (attach files or provide URLs)
- Upload text content as blobs
- Download blobs using their IDs
- List blobs
- Get help

Generate a friendly, helpful clarification message that:
1. Acknowledges their message
2. Explains what you can help them with
3. Asks specific questions to clarify their intent
4. Provides examples of what they can do

Keep the message concise but helpful. Use emojis to make it friendly.
"""


def detect_intent(message: str, has_attachment: bool = False) -> Dict[str, Any]:
    """
    Detect user intent from message text and attachment status.
    
    Args:
        message: User's message text
        has_attachment: Whether the message has a file attachment
        
    Returns:
        Dict with intent classification and extracted data
    """
    
    # If there's an attachment, it's definitely an upload
    if has_attachment:
        return {
            "intent": "upload_file",
            "confidence": 1.0,
            "extracted_data": {
                "blob_id": None,
                "url": None,
                "description": message.strip() if message.strip() else None
            }
        }
    
    # Check for explicit commands first
    message_lower = message.lower().strip()
    
    if message_lower.startswith("/download"):
        blob_id = message[10:].strip() if len(message) > 10 else ""
        return {
            "intent": "download_blob",
            "confidence": 1.0,
            "extracted_data": {
                "blob_id": blob_id if blob_id else None,
                "url": None,
                "description": None
            }
        }
    
    if message_lower.startswith("/upload"):
        description = message[8:].strip() if len(message) > 8 else ""
        return {
            "intent": "upload_text" if description else "upload_file",
            "confidence": 1.0,
            "extracted_data": {
                "blob_id": None,
                "url": None,
                "description": description if description else None
            }
        }
    
    if message_lower.startswith(("/help", "/?", "help")):
        return {
            "intent": "help",
            "confidence": 1.0,
            "extracted_data": {
                "blob_id": None,
                "url": None,
                "description": None
            }
        }
    
    if message_lower.startswith(("/list", "/blobs", "list")):
        return {
            "intent": "list_blobs",
            "confidence": 1.0,
            "extracted_data": {
                "blob_id": None,
                "url": None,
                "description": None
            }
        }
    
    # Check for URLs
    if message.strip().startswith(("http://", "https://")):
        return {
            "intent": "upload_file",
            "confidence": 0.95,
            "extracted_data": {
                "blob_id": None,
                "url": message.strip(),
                "description": None
            }
        }
    
    # Use OpenAI GPT-4 for more complex intent detection
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Upgraded to GPT-4
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this message: '{message}'"}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        # Parse the response
        content = response.choices[0].message.content
        import json
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            pass
            
    except Exception as e:
        print(f"OpenAI intent detection failed: {e}")
    
    # Fallback: if message is short and looks like text, assume upload_text
    if len(message.strip()) < 100 and not any(word in message_lower for word in ["download", "get", "fetch", "retrieve"]):
        return {
            "intent": "upload_text",
            "confidence": 0.7,
            "extracted_data": {
                "blob_id": None,
                "url": None,
                "description": None
            }
        }
    
    # Default to unknown
    return {
        "intent": "unknown",
        "confidence": 0.5,
        "extracted_data": {
            "blob_id": None,
            "url": None,
            "description": None
        }
    }


def generate_clarification_message(user_message: str) -> str:
    """
    Generate a clarification message when user intent is unclear.
    
    Args:
        user_message: The original user message that was unclear
        
    Returns:
        A helpful clarification message
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4 for better clarification
            messages=[
                {"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"User message: '{user_message}'\n\nGenerate a clarification message."}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Failed to generate clarification message: {e}")
        # Fallback clarification message
        return """🤔 I'm not quite sure what you'd like me to do!

I can help you with:
• 📤 **Upload files** - Attach a file or send me a URL
• 📝 **Upload text** - Send me any text to store as a blob
• 📥 **Download blobs** - Use `/download <blob_id>` to get a file
• 📋 **List blobs** - Use `/list` to see your stored files
• ❓ **Get help** - Use `/help` for more info

Could you clarify what you'd like to do? For example:
- "Upload this file" (with attachment)
- "https://example.com/file.mp3" (upload from URL)
- "Hello world!" (upload as text)
- "/download Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24" (download blob)"""


def get_help_message() -> str:
    """Return a helpful message explaining available commands."""
    return """🤖 **Walrus Blob Storage Agent Help**

**Upload Operations:**
• Attach any file to upload it
• Send a URL (http:// or https://) to upload from URL
• Send text to upload as a text blob
• Use `/upload [description]` for explicit upload

**Download Operations:**
• `/download <blob_id>` - Download a specific blob

**Other Commands:**
• `/help` - Show this help message
• `/list` - List your blobs (coming soon)

**Examples:**
• `https://example.com/file.mp3` - Upload from URL
• `Hello world!` - Upload as text blob
• `/download Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24` - Download blob

The agent will automatically detect your intent and perform the appropriate operation! 🚀""" 