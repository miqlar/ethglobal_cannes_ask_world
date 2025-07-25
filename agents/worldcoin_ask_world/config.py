"""
Configuration settings for the Worldcoin AskWorld agent.
"""

import os

# Walrus agent address for blob transcription
WALRUS_AGENT_ADDRESS = os.getenv("WALRUS_AGENT_ADDRESS", "agent1qfxa0vgsvwcp43ykgnysqp5aj2kc90xnxrhphl2jnc34p0p7hkej2srxnsq")

# Voice-to-text agent address (used by Walrus agent)
VOICE_TO_TEXT_AGENT_ADDRESS = os.getenv("VOICE_TO_TEXT_AGENT_ADDRESS", "agent1qvtysj7nswtfa9qun9sjwk39gdnmu3hrc9u2hc66ze374zzmazgtzq05y6z")

# Contract configuration
CONTRACT_ADDRESS = "0xbDBcB9d5f5cF6c6040A7b6151c2ABE25C68f83af"
WORLDCOIN_MAINNET_RPC = "https://worldchain-mainnet.g.alchemy.com/public"

# Agent configuration
AGENT_NAME = "Worldcoin AskWorld Agent"
AGENT_PORT = 8003 