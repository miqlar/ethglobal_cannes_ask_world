"""
Simple chat protocol for the Blockchain Agent.
"""

import os
from datetime import datetime
from uuid import uuid4

from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    MetadataContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

from blockchain_operations import handle_blockchain_request

chat_proto = Protocol(spec=chat_protocol_spec)


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


@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"received message {msg.msg_id} from {sender}")
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(),
                                              acknowledged_msg_id=msg.msg_id))

    user_message = ""

    # Collect content
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            # Tell the UI we support blockchain operations
            await ctx.send(sender, _metadata({"blockchain": "true"}))

        elif isinstance(item, TextContent):
            user_message += item.text + " "

    # Process the message
    user_message = user_message.strip()
    
    if not user_message:
        await ctx.send(sender, _chat("Please provide a function name to call. Type 'help' for available functions."))
        return
    
    # Handle the blockchain request
    try:
        result = await handle_blockchain_request(ctx, user_message)
        await ctx.send(sender, _chat(result))
    except Exception as e:
        error_msg = f"❌ Error processing request: {str(e)}"
        await ctx.send(sender, _chat(error_msg))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"ack from {sender} for {msg.acknowledged_msg_id}") 