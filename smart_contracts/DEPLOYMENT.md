# AskWorld Contract Deployment Guide

This guide explains how to deploy the AskWorld smart contract to different networks using Foundry.

## Prerequisites

1. **Foundry Installation**: Make sure you have Foundry installed
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

2. **Environment Setup**: Set up your environment variables

## Environment Variables

Create a `.env` file in the `smart_contracts` directory with the following variables:

```bash
# Private key for deployment (without 0x prefix)
PRIVATE_KEY=your_private_key_here

# RPC URLs for different networks
ETHEREUM_SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
WORLDCHAIN_SEPOLIA_RPC_URL=https://worldchain-sepolia.drpc.org

# Initial AI validator address (optional, defaults to deployer)
INITIAL_AI_VALIDATOR=0x...

# API keys for contract verification
ETHERSCAN_API_KEY=your_etherscan_api_key_here
BASESCAN_API_KEY=your_basescan_api_key_here
WORLDCOIN_API_KEY=your_worldcoin_api_key_here
```

## Deployment Options

### 1. Local Deployment (Anvil)

Deploy to a local Anvil network for testing:

```bash
./deploy.sh local
```

This will:
- Start a local Anvil network
- Deploy the contract using the default test account
- Add the deployer as an AI validator
- Save deployment information

### 2. Testnet Deployment

Deploy to a testnet (Sepolia, Base Sepolia, or Worldcoin Sepolia):

```bash
# Ethereum Sepolia
./deploy.sh sepolia 0xyour_private_key_here

# Base Sepolia
./deploy.sh base-sepolia 0xyour_private_key_here

# Worldcoin Sepolia
./deploy.sh worldcoin-sepolia 0xyour_private_key_here
```

### 3. Manual Deployment

You can also deploy manually using Foundry commands:

```bash
# Build the contract
forge build

# Deploy using the script
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url $RPC_URL \
  --private-key $PRIVATE_KEY \
  --broadcast \
  --verify
```

## Deployment Script Features

The deployment script (`script/Deploy.s.sol`) includes:

- **Environment-based configuration**: Reads from environment variables
- **Initial AI validator setup**: Automatically adds the initial AI validator
- **Deployment logging**: Comprehensive logging of the deployment process
- **Deployment info saving**: Saves deployment details to `deployment-info.txt`
- **Network validation**: Validates RPC URLs and network configuration

## Post-Deployment

After deployment, the script will:

1. Display the contract address
2. Show the owner address
3. Confirm AI validator status
4. Save deployment information to `deployment-info.txt`

## Contract Verification

The deployment script includes automatic contract verification. Make sure to set the appropriate API keys:

- **Etherscan**: For Ethereum Sepolia
- **BaseScan**: For Base Sepolia
- **Worldcoin**: For Worldcoin Sepolia

## Security Considerations

1. **Private Key Security**: Never commit your private key to version control
2. **Environment Variables**: Use `.env` files and add them to `.gitignore`
3. **Network Selection**: Double-check the network before deployment
4. **Gas Estimation**: Monitor gas costs during deployment

## Troubleshooting

### Common Issues

1. **"Foundry not installed"**: Install Foundry using the official installer
2. **"Invalid private key"**: Ensure your private key is 64 hex characters with 0x prefix
3. **"RPC URL not set"**: Set the appropriate environment variable for your network
4. **"Insufficient funds"**: Ensure your account has enough ETH for deployment

### Getting Help

- Check the Foundry documentation: https://getfoundry.sh/
- Review the deployment logs for specific error messages
- Verify your environment variables are set correctly

## Example Deployment Output

```
[INFO] AskWorld Contract Deployment
[INFO] ============================
[INFO] Using Ethereum Sepolia testnet
[INFO] Building contract...
[SUCCESS] Contract built successfully
[INFO] Deploying AskWorld contract to sepolia...
[SUCCESS] Deployment completed!
[INFO] Deployment information:
Deployment Info:
================
Contract: AskWorld
Address: 0x1234567890abcdef...
Deployer: 0xabcdef1234567890...
Owner: 0xabcdef1234567890...
Initial AI Validator: 0xabcdef1234567890...
Network: https://sepolia.infura.io/v3/...
Block: 1234567
Timestamp: 1234567890
[SUCCESS] Deployment process completed! 