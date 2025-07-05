"""
Walrus Blob Storage uAgent entrypoint.
"""

from uagents import Agent
from chat_proto import chat_proto
from agent_communication import agent_comm_proto
from shared_models import (
    BlobUploadRequest, BlobUploadResponse,
    BlobUploadFromUrlRequest, BlobUploadFromUrlResponse,
    TextUploadRequest, TextUploadResponse,
    BlobDownloadRequest, BlobDownloadResponse
)

# Configure agent for mailbox mode
SEED_PHRASE = "put_your_seed_phrase_here"

agent = Agent(
    name="walrus-storage",
    port=8001,  # Using 8001 to avoid conflicts with other agents
    #endpoint=["http://localhost:8001/submit"],
    mailbox=True
)

# Include chat protocol and publish manifest so ASI:One / Agentverse can find it
agent.include(chat_proto, publish_manifest=True)

# Include agent communication protocol
agent.include(agent_comm_proto)

# Add REST endpoints for direct testing

@agent.on_rest_post("/upload", BlobUploadRequest, BlobUploadResponse)
async def handle_upload_rest(ctx, req: BlobUploadRequest) -> BlobUploadResponse:
    """REST endpoint for blob upload."""
    ctx.logger.info(f"Received REST upload request")
    
    try:
        import base64
        from walrus_operations import _upload_resource
        
        # Decode base64 data
        data = base64.b64decode(req.data_base64)
        
        # Upload to walrus
        result = _upload_resource(data, req.mime_type)
        
        # Parse the result to extract blob_id and url
        if "✅ File uploaded successfully!" in result:
            # Extract blob_id and url from the result string
            lines = result.split('\n')
            blob_id = None
            blob_url = None
            for line in lines:
                if line.startswith("Blob ID: "):
                    blob_id = line.replace("Blob ID: ", "").strip()
                elif line.startswith("View at: "):
                    blob_url = line.replace("View at: ", "").strip()
            
            if blob_id and blob_url:
                return BlobUploadResponse(
                    blob_id=blob_id,
                    blob_url=blob_url,
                    success=True
                )
        
        return BlobUploadResponse(
            blob_id="",
            blob_url="",
            success=False,
            error_message=result
        )
        
    except Exception as exc:
        ctx.logger.error(f"Upload failed: {exc}")
        return BlobUploadResponse(
            blob_id="",
            blob_url="",
            success=False,
            error_message=str(exc)
        )


@agent.on_rest_post("/upload-url", BlobUploadFromUrlRequest, BlobUploadFromUrlResponse)
async def handle_upload_url_rest(ctx, req: BlobUploadFromUrlRequest) -> BlobUploadFromUrlResponse:
    """REST endpoint for blob upload from URL."""
    ctx.logger.info(f"Received REST upload from URL request: {req.url}")
    
    try:
        from walrus_operations import _upload_file_from_url
        
        # Upload from URL
        result = _upload_file_from_url(req.url)
        
        # Parse the result to extract blob_id and url
        if "✅ File uploaded successfully!" in result:
            lines = result.split('\n')
            blob_id = None
            blob_url = None
            for line in lines:
                if line.startswith("Blob ID: "):
                    blob_id = line.replace("Blob ID: ", "").strip()
                elif line.startswith("View at: "):
                    blob_url = line.replace("View at: ", "").strip()
            
            if blob_id and blob_url:
                return BlobUploadFromUrlResponse(
                    blob_id=blob_id,
                    blob_url=blob_url,
                    success=True
                )
        
        return BlobUploadFromUrlResponse(
            blob_id="",
            blob_url="",
            success=False,
            error_message=result
        )
        
    except Exception as exc:
        ctx.logger.error(f"Upload from URL failed: {exc}")
        return BlobUploadFromUrlResponse(
            blob_id="",
            blob_url="",
            success=False,
            error_message=str(exc)
        )


@agent.on_rest_post("/upload-text", TextUploadRequest, TextUploadResponse)
async def handle_upload_text_rest(ctx, req: TextUploadRequest) -> TextUploadResponse:
    """REST endpoint for text upload."""
    ctx.logger.info(f"Received REST text upload request")
    
    try:
        from walrus_operations import client
        
        # Upload text as blob
        blob_data = req.text.encode('utf-8')
        response = client.put_blob(data=blob_data)
        blob_id = response['newlyCreated']['blobObject']['blobId']
        blob_url = f"https://walruscan.com/testnet/blob/{blob_id}"
        
        return TextUploadResponse(
            blob_id=blob_id,
            blob_url=blob_url,
            success=True
        )
        
    except Exception as exc:
        ctx.logger.error(f"Text upload failed: {exc}")
        return TextUploadResponse(
            blob_id="",
            blob_url="",
            success=False,
            error_message=str(exc)
        )


@agent.on_rest_post("/download", BlobDownloadRequest, BlobDownloadResponse)
async def handle_download_rest(ctx, req: BlobDownloadRequest) -> BlobDownloadResponse:
    """REST endpoint for blob download."""
    ctx.logger.info(f"Received REST download request for blob {req.blob_id}")
    
    try:
        import base64
        from walrus_operations import _download_blob_data
        
        # Download blob data
        blob_data, mime_type = _download_blob_data(req.blob_id)
        
        # Encode as base64
        blob_data_base64 = base64.b64encode(blob_data).decode('utf-8')
        
        return BlobDownloadResponse(
            blob_data_base64=blob_data_base64,
            mime_type=mime_type,
            blob_id=req.blob_id,
            request_id=req.request_id,
            success=True
        )
        
    except Exception as exc:
        ctx.logger.error(f"Download failed for blob {req.blob_id}: {exc}")
        return BlobDownloadResponse(
            blob_data_base64="",
            mime_type="",
            blob_id=req.blob_id,
            request_id=req.request_id,
            success=False,
            error_message=str(exc)
        )

# Copy the address shown below
print(f"Your agent's address is: {agent.address}")

if __name__ == "__main__":
    agent.run() 