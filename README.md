# AskWorld - ETHGlobal Cannes 2025

<p align="center">
  <img src="img/askworld.png" alt="AskWorld Logo" width="300">
</p>

## Summary

A decentralized Q&A platform where users can ask questions with bounties and receive audio answers. AskWorld leverages AI validation, blockchain storage, and multi-agent architecture to create a trustless system for knowledge sharing and monetization.

Users submit audio answers to questions, which are automatically stored on Walrus (decentralized data storage), transcribed by voice agents, and validated by AI agents on Agentverse. The settlement layer for payments and platform management is handled by smart contracts deployed on WorldChain. Valid answers receive bounty payments, creating a sustainable ecosystem for knowledge exchange.

## Deployed Contracts

| Network | Address | Verified |
| --------------- | --------------- | --- |
| WorldChain Mainnet | [0xbDBcB9d5f5cF6c6040A7b6151c2ABE25C68f83af](https://worldscan.org/address/0xbDBcB9d5f5cF6c6040A7b6151c2ABE25C68f83af) | :white_check_mark: |

## Repository Structure

```
ethglobal_cannes_ask_world/
├── agents/                    # Multi-agent system
│   ├── voice_transcriber/     # Audio transcription agent
│   ├── walrus/               # Data Storage Agent 
│   └── worldcoin_ask_world/  # AskWorld contract manager agent + validator
├── ask-world/                # Main Next.js frontend
├── ask-world-legacy/         # Legacy frontend version
├── smart_contracts/          # Foundry smart contracts
├── sui_faucet/              # Sui blockchain utilities
├── tests/                   # Random tests
├── img/                     # Project assets
└── README.md                # Project documentation
```

### Key Components

- **agents/**: Three self-contained agents working together:
  - **voice_transcriber/**: Converts audio to text
  - **walrus/**: Fetches and stores blobs in the walrus data system
  - **worldcoin_ask_world/**: Handles blockchain operations, validates
- **ask-world/**: Modern Next.js frontend with audio recording and blockchain integration
- **smart_contracts/**: Foundry-based smart contracts for bounty management
- **sui_faucet/**: Utilities for Sui blockchain testing
- **tests/**: Testing suite for all components