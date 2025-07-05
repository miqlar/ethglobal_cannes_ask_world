"""
Chat protocol for the Walrus Blob Storage Agent.

Flow:
  • announce attachment support
  • pull file data (resource or URL string)
  • call walrus operations (upload/download)
"""

import os
from datetime import datetime
from uuid import uuid4

from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    MetadataContent,
    ResourceContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.storage import ExternalStorage

from walrus_operations import handle_walrus_operation
from intent_detection import detect_intent, get_help_message, generate_clarification_message

STORAGE_URL = os.getenv("AGENTVERSE_URL", "https://agentverse.ai") + "/v1/storage"


def _chat(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    )


def _metadata(meta: dict[str, str]) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[MetadataContent(type="metadata", metadata=meta)],
    )


chat_proto = Protocol(spec=chat_protocol_spec)


@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"received message {msg.msg_id} from {sender}")
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(),
                                              acknowledged_msg_id=msg.msg_id))

    prompt_content = []
    has_attachment = False
    user_message = ""

    # First pass: collect content and check for attachments
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            # Tell the UI we support uploads
            await ctx.send(sender, _metadata({"attachments": "true"}))

        elif isinstance(item, TextContent):
            user_message += item.text + " "

        elif isinstance(item, ResourceContent):
            has_attachment = True
            try:
                storage = ExternalStorage(identity=ctx.agent.identity,
                                          storage_url=STORAGE_URL)
                data = storage.download(str(item.resource_id))
                prompt_content.append({
                    "type": "resource",
                    "mime_type": data["mime_type"],
                    "contents": data["contents"],
                })
            except Exception as exc:
                ctx.logger.error(f"download error: {exc}")
                await ctx.send(sender, _chat("Failed to download the attachment."))

    # Detect intent using OpenAI
    user_message = user_message.strip()
    intent_result = detect_intent(user_message, has_attachment)
    
    ctx.logger.info(f"Detected intent: {intent_result['intent']} (confidence: {intent_result['confidence']})")
    
    # Check if intent is unclear (low confidence or unknown)
    confidence = intent_result.get('confidence', 0.0)
    intent = intent_result.get('intent', 'unknown')
    
    # If confidence is low or intent is unknown, ask for clarification
    if confidence < 0.7 or intent == 'unknown':
        if user_message:  # Only ask for clarification if there's a message
            clarification = generate_clarification_message(user_message)
            await ctx.send(sender, _chat(clarification))
        else:
            await ctx.send(sender, _chat("No message provided. Try sending a message or attaching a file!"))
        return
    
    # Handle different intents
    if intent == 'help':
        await ctx.send(sender, _chat(get_help_message()))
        return
    
    elif intent == 'list_blobs':
        await ctx.send(sender, _chat("📋 Blob listing feature coming soon! For now, you can use the blob ID from previous uploads to download files."))
        return
    
    # For upload and download operations, add text content if needed
    if user_message and intent in ['upload_file', 'upload_text']:
        # Add the user message as text content
        prompt_content.append({"type": "text", "text": user_message})
    
    # Handle the operation based on intent
    if prompt_content or intent in ['upload_text', 'download_blob']:
        result = await handle_walrus_operation(prompt_content, intent_result, ctx)
        await ctx.send(sender, _chat(result))
    else:
        await ctx.send(sender, _chat("No content provided. Try attaching a file or sending a message!"))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"ack from {sender} for {msg.acknowledged_msg_id}") 