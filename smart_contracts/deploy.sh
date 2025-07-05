#!/bin/bash

# AskWorld Contract Deployment Script
# Usage: ./deploy.sh [network] [private_key]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NETWORK=${1:-"local"}
PRIVATE_KEY=${2:-""}
RPC_URL=""
CHAIN_ID=""

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if forge is installed
if ! command_exists forge; then
    print_error "Foundry is not installed. Please install it first: https://getfoundry.sh/"
    exit 1
fi

# Function to set network configuration
set_network_config() {
    case $NETWORK in
        "local"|"anvil")
            RPC_URL="http://localhost:8545"
            CHAIN_ID="31337"
            print_info "Using local Anvil network"
            ;;
        "sepolia")
            RPC_URL=${ETHEREUM_SEPOLIA_RPC_URL:-"https://ethereum-sepolia-rpc.publicnode.com"}
            CHAIN_ID="11155111"
            print_info "Using Ethereum Sepolia testnet"
            ;;
        "base-sepolia")
            RPC_URL=${BASE_SEPOLIA_RPC_URL:-"https://base-sepolia-rpc.publicnode.com"}
            CHAIN_ID="84532"
            print_info "Using Base Sepolia testnet"
            ;;
        "worldcoin-sepolia")
            RPC_URL=${WORLDCHAIN_SEPOLIA_RPC_URL:-"https://worldchain-sepolia.drpc.org"}
            CHAIN_ID="11155420"
            print_info "Using Worldcoin Sepolia testnet"
            ;;
        "worldcoin-mainnet")
            RPC_URL=${WORLDCHAIN_MAINNET_RPC_URL:-"https://worldchain-mainnet.g.alchemy.com/public"}
            CHAIN_ID="480"
            print_info "Using Worldcoin mainnet"
            ;;
        *)
            print_error "Unknown network: $NETWORK"
            print_info "Available networks: local, sepolia, base-sepolia, worldcoin-sepolia, worldcoin-mainnet"
            exit 1
            ;;
    esac
}

# Function to validate private key
validate_private_key() {
    if [[ -z "$PRIVATE_KEY" ]]; then
        if [[ "$NETWORK" == "local" ]]; then
            # Use default Anvil private key for local deployment
            PRIVATE_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
            print_warning "Using default Anvil private key for local deployment"
        else
            print_error "Private key is required for network deployment"
            print_info "Usage: ./deploy.sh [network] [private_key]"
            print_info "Example: ./deploy.sh sepolia 0x1234567890abcdef..."
            exit 1
        fi
    fi
    
    # Basic private key validation (64 hex characters)
    if [[ ! "$PRIVATE_KEY" =~ ^0x[a-fA-F0-9]{64}$ ]]; then
        print_error "Invalid private key format. Must be 64 hex characters with 0x prefix"
        exit 1
    fi
}

# Function to check environment variables
check_environment() {
    if [[ "$NETWORK" != "local" ]]; then
        if [[ -z "$RPC_URL" ]]; then
            print_error "RPC URL not set for network: $NETWORK"
            print_info "Please set the appropriate environment variable:"
            case $NETWORK in
                "sepolia")
                    print_info "export ETHEREUM_SEPOLIA_RPC_URL=your_rpc_url"
                    ;;
                "base-sepolia")
                    print_info "export BASE_SEPOLIA_RPC_URL=your_rpc_url"
                    ;;
                "worldcoin-sepolia")
                    print_info "export WORLDCHAIN_SEPOLIA_RPC_URL=your_rpc_url"
                    ;;
                "worldcoin-mainnet")
                    print_info "export WORLDCHAIN_MAINNET_RPC_URL=your_rpc_url"
                    ;;
            esac
            exit 1
        fi
    fi
}

# Function to build the contract
build_contract() {
    print_info "Building contract..."
    forge build --force
    print_success "Contract built successfully"
}

# Function to deploy the contract
deploy_contract() {
    print_info "Deploying AskWorld contract to $NETWORK..."
    
    # Set environment variables for the script
    export PRIVATE_KEY=$PRIVATE_KEY
    export RPC_URL=$RPC_URL
    
    # Deploy using Foundry script
    if [[ "$NETWORK" == "local" ]]; then
        # For local deployment, use the test script
        forge script script/Deploy.s.sol:DeployTestScript --rpc-url $RPC_URL --broadcast --verify
    else
        # For network deployment, use the main script
        forge script script/Deploy.s.sol:DeployScript --rpc-url $RPC_URL --broadcast --verify
    fi
    
    print_success "Deployment completed!"
}

# Function to verify deployment
verify_deployment() {
    print_info "Deployment completed successfully!"
    print_info "Check the logs above for deployment information."
}

# Function to start local network
start_local_network() {
    if [[ "$NETWORK" == "local" ]]; then
        print_info "Starting local Anvil network..."
        anvil --port 8545 &
        ANVIL_PID=$!
        sleep 2
        print_success "Local network started (PID: $ANVIL_PID)"
    fi
}

# Function to cleanup
cleanup() {
    if [[ ! -z "$ANVIL_PID" ]]; then
        print_info "Stopping local network..."
        kill $ANVIL_PID 2>/dev/null || true
    fi
}

# Main execution
main() {
    print_info "AskWorld Contract Deployment"
    print_info "============================"
    
    # Set network configuration
    set_network_config
    
    # Validate private key
    validate_private_key
    
    # Check environment
    check_environment
    
    # Build contract
    build_contract
    
    # Start local network if needed
    start_local_network
    
    # Deploy contract
    deploy_contract
    
    # Verify deployment
    verify_deployment
    
    print_success "Deployment process completed!"
}

# Trap to cleanup on exit
trap cleanup EXIT

# Run main function
main "$@" 