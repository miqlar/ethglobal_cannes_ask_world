# AskWorld - ETHGlobal Cannes 2025

<p align="center">
  <img src="img/askworld.png" alt="AskWorld Logo" width="300">
</p>

## Summary

A decentralized Q&A platform where users can ask questions with bounties and receive audio answers. AskWorld leverages AI validation, blockchain storage, and multi-agent architecture to create a trustless system for knowledge sharing and monetization.

Users submit audio answers to questions, which are automatically transcribed, validated by AI, and stored on the Worldcoin mainnet blockchain. Valid answers receive bounty payments, creating a sustainable ecosystem for knowledge exchange.

## Deployed Contracts

| Network | Address | Explorer |
| --------------- | --------------- | --- |
| WorldChain Mainnet | [0x5549A2E7a5b6eE6B556C0EE5eF5256B7c4eD46D6](https://worldscan.org/address/0x5549a2e7a5b6ee6b556c0ee5ef5256b7c4ed46d6) | :white_check_mark: |

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