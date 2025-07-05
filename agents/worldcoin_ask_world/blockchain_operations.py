"""
Simple blockchain operations for reading from a specific Worldcoin Sepolia contract.
"""

import os
from typing import Any
from dotenv import load_dotenv
from web3 import Web3

load_dotenv("../.env")

# Worldcoin Sepolia configuration
WORLDCOIN_SEPOLIA_RPC = os.getenv("WORLDCOIN_SEPOLIA_RPC", "https://worldchain-sepolia.drpc.org")

# Contract configuration
CONTRACT_ADDRESS = "0x4bf06d1F01ba06b84F97efA2883Ea2aC46752cc4"
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"inputs":[],"name":"InvalidInitialization","type":"error"},
    {"inputs":[],"name":"NotInitializing","type":"error"},
    {"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint64","name":"version","type":"uint64"}],"name":"Initialized","type":"event"},
    {"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"string","name":"_secret","type":"string"}],"name":"found","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"address","name":"_owner","type":"address"},{"internalType":"address","name":"_secretHash","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"isFound","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"isLost","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"isReturned","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"lost","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"returned","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"secretHash","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(WORLDCOIN_SEPOLIA_RPC))

# Initialize contract
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# Available read functions (view functions only)
READ_FUNCTIONS = [
    "factory",
    "isFound", 
    "isLost",
    "isReturned",
    "owner",
    "secretHash"
]


def check_connection() -> str:
    """Check if we can connect to the Worldcoin Sepolia network."""
    try:
        if w3.is_connected():
            latest_block = w3.eth.block_number
            return f"✅ Connected to Worldcoin Sepolia!\n📊 Latest block: {latest_block}\n🔗 Contract: {CONTRACT_ADDRESS}"
        else:
            return f"❌ Failed to connect to Worldcoin Sepolia at {WORLDCOIN_SEPOLIA_RPC}"
    except Exception as e:
        return f"❌ Connection error: {e}"


def read_function(function_name: str) -> str:
    """
    Read a specific function from the contract.
    
    Args:
        function_name: Name of the function to call
        
    Returns:
        String with the result or error message
    """
    try:
        # Check if function exists and is readable
        if function_name not in READ_FUNCTIONS:
            return f"❌ Function '{function_name}' not found or not readable.\n📋 Available functions: {', '.join(READ_FUNCTIONS)}"
        
        # Call the function
        result = getattr(contract.functions, function_name)().call()
        
        # Format the result
        if isinstance(result, bool):
            return f"✅ {function_name}() = {result}"
        elif isinstance(result, str):
            return f"✅ {function_name}() = '{result}'"
        elif isinstance(result, int):
            # Check if it's an address (42 chars when converted to hex)
            if result > 0 and len(hex(result)) == 42:
                return f"✅ {function_name}() = 0x{result:040x}"
            else:
                return f"✅ {function_name}() = {result}"
        else:
            return f"✅ {function_name}() = {result}"
        
    except Exception as e:
        return f"❌ Error calling {function_name}: {e}"


def get_available_functions() -> str:
    """Get list of available read functions."""
    return f"📋 Available read functions:\n" + "\n".join([f"• {func}" for func in READ_FUNCTIONS])


def handle_blockchain_request(function_name: str) -> str:
    """
    Handle blockchain requests.
    
    Args:
        function_name: Name of the function to call
        
    Returns:
        String with the result
    """
    function_name = function_name.strip()
    
    if function_name.lower() in ["connection", "connect", "network", "status"]:
        return check_connection()
    
    elif function_name.lower() in ["help", "functions", "list"]:
        return get_available_functions()
    
    else:
        return read_function(function_name) 