"""
Audio-to-Text uAgent entrypoint.
"""

from uagents import Agent
from chat_proto import chat_proto

agent = Agent()

# Include chat protocol and publish manifest so ASI:One / Agentverse can find it
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
