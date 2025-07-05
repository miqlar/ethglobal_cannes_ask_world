# Simple Blockchain Agent - Worldcoin Sepolia Reader

A simple uAgent that reads from a specific smart contract on the Worldcoin Sepolia blockchain.

## Contract Details

- **Address**: `0x4bf06d1F01ba06b84F97efA2883Ea2aC46752cc4`
- **Network**: Worldcoin Sepolia Testnet
- **RPC**: https://worldchain-sepolia.drpc.org

## Available Read Functions

- `factory` - Get factory address
- `isFound` - Check if found
- `isLost` - Check if lost  
- `isReturned` - Check if returned
- `owner` - Get owner address
- `secretHash` - Get secret hash address

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the agent:
```bash
python agent.py
```

## Usage

Simply input the function name you want to call:

### Chat Interface
- `factory` - Get factory address
- `isFound` - Check if found
- `owner` - Get owner address
- `help` - Show available functions
- `connection` - Check network connection

### REST API
- `POST /call` - Call a function
  ```json
  {
    "function_name": "isFound"
  }
  ```

## Examples

### Chat Examples
- User: `factory`
- Agent: `✅ factory() = 0x1234567890123456789012345678901234567890`

- User: `isFound`
- Agent: `✅ isFound() = true`

- User: `owner`
- Agent: `✅ owner() = 0xabcdef1234567890abcdef1234567890abcdef12`

### REST API Example
```bash
curl -X POST http://localhost:8003/call \
  -H "Content-Type: application/json" \
  -d '{"function_name": "isFound"}'
```

Response:
```json
{
  "function_name": "isFound",
  "result": "✅ isFound() = true",
  "success": true
}
```

## Response Format

All responses follow the format: 