"""
Chat protocol for the Audio-to-Text Agent.

Same flow as your image agent:
  • announce attachment support
  • pull audio data (resource or URL string)
  • call get_audio_transcription
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

from audio_analysis import get_audio_transcription

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

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            # Tell the UI we support uploads
            await ctx.send(sender, _metadata({"attachments": "true"}))

        elif isinstance(item, TextContent):
            prompt_content.append({"type": "text", "text": item.text})

        elif isinstance(item, ResourceContent):
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

    if prompt_content:
        transcript = get_audio_transcription(prompt_content)
        await ctx.send(sender, _chat(transcript))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"ack from {sender} for {msg.acknowledged_msg_id}")
