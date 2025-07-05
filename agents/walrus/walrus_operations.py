"""
Walrus blob storage operations.

Requirements
------------
pip install walrus-python requests python-dotenv
# + uagents if you run the full agent
"""

import base64
import os
import tempfile
from typing import Any, List, Dict
import requests
from dotenv import load_dotenv
from walrus import WalrusClient

load_dotenv("../.env")

# Walrus configuration
PUBLISHER_URL = os.getenv("WALRUS_PUBLISHER_URL", "https://publisher.walrus-testnet.walrus.space")
AGGREGATOR_URL = os.getenv("WALRUS_AGGREGATOR_URL", "https://aggregator.walrus-testnet.walrus.space")

client = WalrusClient(publisher_base_url=PUBLISHER_URL, aggregator_base_url=AGGREGATOR_URL)


def _save_to_temp(data: bytes, suffix: str) -> str:
    """Write bytes to a temporary file and return the path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data)
    tmp.close()
    return tmp.name


def _upload_file_from_url(url: str) -> str:
    """Download file from URL and upload to Walrus."""
    try:
        print(f"[walrus-agent] Fetching file from: {url}")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            # Infer an extension, default to .bin
            suffix = os.path.splitext(url)[-1] or ".bin"
            path = _save_to_temp(r.content, suffix)
        
        response = client.put_blob_from_file(path)
        os.remove(path)
        
        blob_id = response['newlyCreated']['blobObject']['blobId']
        blob_url = f"https://walruscan.com/testnet/blob/{blob_id}"
        
        return f"""✅ **File Uploaded Successfully!**

📋 **Details:**
• **Blob ID:** `{blob_id}`
• **View at:** {blob_url}"""
        
    except requests.exceptions.RequestException as exc:
        return f"""❌ **Upload Failed**

Could not download file from URL: {exc}"""
    except Exception as exc:
        return f"""❌ **Upload Failed**

Error: {exc}"""


def _upload_resource(data: bytes, mime_type: str) -> str:
    """Upload resource data to Walrus."""
    try:
        # Determine file extension from mime type
        ext_map = {
            "audio/": ".audio",
            "image/": ".image", 
            "video/": ".video",
            "text/": ".txt",
            "application/pdf": ".pdf",
            "application/json": ".json",
        }
        
        suffix = ".bin"  # default
        for prefix, ext in ext_map.items():
            if mime_type.startswith(prefix):
                suffix = ext
                break
        
        path = _save_to_temp(data, suffix)
        response = client.put_blob_from_file(path)
        os.remove(path)
        
        blob_id = response['newlyCreated']['blobObject']['blobId']
        blob_url = f"https://walruscan.com/testnet/blob/{blob_id}"
        
        return f"""✅ **File Uploaded Successfully!**

📋 **Details:**
• **Blob ID:** `{blob_id}`
• **View at:** {blob_url}"""
        
    except Exception as exc:
        return f"""❌ **Upload Failed**

Error: {exc}"""


def _download_blob_data(blob_id: str) -> tuple[bytes, str]:
    """Download blob data from Walrus and return bytes and mime type."""
    try:
        # Create a temporary file for download
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".downloaded")
        tmp.close()
        
        client.get_blob_as_file(blob_id, tmp.name)
        
        # Read the file data
        with open(tmp.name, 'rb') as f:
            blob_data = f.read()
        
        # Try to determine mime type from file extension and content
        mime_type = "application/octet-stream"  # default
        
        # Check file extension first
        import mimetypes
        file_extension = os.path.splitext(tmp.name)[1]
        if file_extension:
            detected_mime = mimetypes.guess_type(f"file{file_extension}")[0]
            if detected_mime:
                mime_type = detected_mime
        
        # If still default, try to detect from blob_id or content
        if mime_type == "application/octet-stream":
            # Check if blob_id contains audio file extensions
            if any(ext in blob_id.lower() for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']):
                mime_type = "audio/mpeg"  # Default audio type
            # Check file magic bytes for common audio formats
            elif blob_data.startswith(b'ID3') or blob_data.startswith(b'\xff\xfb'):
                mime_type = "audio/mpeg"  # MP3
            elif blob_data.startswith(b'RIFF'):
                mime_type = "audio/wav"   # WAV
            elif blob_data.startswith(b'ftyp'):
                mime_type = "audio/mp4"   # M4A
        
        # Clean up the temporary file
        os.remove(tmp.name)
        
        return blob_data, mime_type
        
    except Exception as exc:
        raise Exception(f"Download failed: {exc}")


async def _download_blob(blob_id: str, ctx=None) -> str:
    """Download blob from Walrus."""
    try:
        # Download blob data
        blob_data, mime_type = _download_blob_data(blob_id)
        
        # Get file size
        file_size = len(blob_data)
        
        # Format file size nicely
        if file_size > 1024 * 1024:
            file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            file_size_str = f"{file_size / 1024:.1f} KB"
        else:
            file_size_str = f"{file_size} bytes"
        
        result = f"""✅ **Blob Downloaded Successfully!**

📋 **Details:**
• **Blob ID:** `{blob_id}`
• **File Size:** {file_size_str}
• **MIME Type:** {mime_type}"""
        
        # Check if it's an audio file and trigger transcription
        is_audio = (
            mime_type.startswith("audio/") or 
            any(ext in blob_id.lower() for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']) or
            blob_data.startswith(b'ID3') or  # MP3
            blob_data.startswith(b'\xff\xfb') or  # MP3
            blob_data.startswith(b'RIFF') or  # WAV
            blob_data.startswith(b'ftyp')  # M4A
        )
        
        if ctx and is_audio:
            result += f"""

🎵 **Audio File Detected!**
Requesting transcription..."""
            
            # Import here to avoid circular imports
            from agent_communication import request_audio_transcription
            transcription_result = await request_audio_transcription(ctx, blob_data, mime_type, blob_id)
            if transcription_result:
                result += transcription_result
        
        return result
        
    except Exception as exc:
        return f"❌ **Download Failed**\n\nError: {exc}"


async def handle_walrus_operation(content: List[Dict[str, Any]], intent_result: Dict[str, Any], ctx=None) -> str:
    """
    Accepts ChatMessage `content` list and intent result, returns the operation result.
    
    Supports:
      • {"type": "resource", "mime_type": "...", "contents": <base64>} - Upload file
      • {"type": "text", "text": "https://example.com/file.mp3"} - Upload from URL
      • {"type": "text", "text": "some text"} - Upload as text blob
      • Intent-based operations for download and other actions
    """
    
    intent = intent_result.get("intent", "unknown")
    extracted_data = intent_result.get("extracted_data", {})
    
    # Handle download operation
    if intent == "download_blob":
        blob_id = extracted_data.get("blob_id")
        if not blob_id:
            # Try to extract from content
            for item in content:
                if item.get("type") == "text" and item["text"].startswith("blob_id:"):
                    blob_id = item["text"][8:]  # Remove "blob_id:" prefix
                    break
        
        if blob_id:
            return await _download_blob(blob_id, ctx)
        else:
            return """❌ **No Valid Blob ID Provided**

Please use the format: `/download <blob_id>`"""
    
    # Handle upload operations
    results = []
    
    # Handle attached files
    for item in content:
        if item.get("type") == "resource":
            # Upload attached file
            data = base64.b64decode(item["contents"])
            results.append(_upload_resource(data, item["mime_type"]))
    
    # Handle text content based on intent
    for item in content:
        if item.get("type") == "text":
            text = item["text"].strip()
            
            if text.startswith(("http://", "https://")):
                # Upload from URL
                results.append(_upload_file_from_url(text))
            elif intent == "upload_text" or (intent == "upload_file" and not text.startswith(("http://", "https://"))):
                # Upload as text blob (but skip if it's just a URL)
                if text and not text.startswith(("http://", "https://")):
                    try:
                        blob_data = text.encode('utf-8')
                        response = client.put_blob(data=blob_data)
                        blob_id = response['newlyCreated']['blobObject']['blobId']
                        blob_url = f"https://walruscan.com/testnet/blob/{blob_id}"
                        results.append(f"""✅ **Text Uploaded Successfully!**

📋 **Details:**
• **Blob ID:** `{blob_id}`
• **View at:** {blob_url}""")
                    except Exception as exc:
                        results.append(f"""❌ **Text Upload Failed**

Error: {exc}""")
    
    # If no content but intent is upload_text, try to use extracted data
    if not results and intent == "upload_text":
        description = extracted_data.get("description")
        if description:
            try:
                blob_data = description.encode('utf-8')
                response = client.put_blob(data=blob_data)
                blob_id = response['newlyCreated']['blobObject']['blobId']
                blob_url = f"https://walruscan.com/testnet/blob/{blob_id}"
                results.append(f"""✅ **Text Uploaded Successfully!**

📋 **Details:**
• **Blob ID:** `{blob_id}`
• **View at:** {blob_url}""")
            except Exception as exc:
                results.append(f"""❌ **Text Upload Failed**

Error: {exc}""")
    
    return "\n\n".join(results) if results else """❌ **No Valid Content Found**

Please provide a file, URL, or text to upload.""" 