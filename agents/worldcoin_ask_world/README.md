# Simple Blockchain Agent - Worldcoin Mainnet AskWorld Reader

A simple uAgent that reads from the AskWorld smart contract on the Worldcoin Mainnet blockchain.

## Contract Details

- **Address**: `0x185591a5DC4B65B8B7AF5befca02C702F23C476C`
- **Network**: Worldcoin Mainnet
- **RPC**: https://worldchain-mainnet.g.alchemy.com/public
- **Contract**: AskWorld - A smart contract for managing questions with audio answers and AI validation

## Available Read Functions

### Basic Statistics
- `owner` - Get contract owner address
- `totalQuestions` - Get total number of questions
- `totalAnswers` - Get total number of answers
- `totalValidAnswers` - Get total number of valid answers
- `getContractStats` - Get comprehensive contract statistics

### Question Management
- `getOpenQuestions` - Get list of open question IDs
- `getQuestion(questionId)` - Get detailed question information
- `getQuestionAnswers(questionId)` - Get all answers for a question
- `getQuestionStats(questionId)` - Get statistics for a specific question

### Answer Validation
- `getNextUnvalidatedAnswer` - Get the next answer that needs validation
- `validate` - Process unanswered questions, fetch audio blob ID, and send to Walrus agent for transcription via voice-to-text agent

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

### Chat Interface
- `owner` - Get contract owner
- `totalQuestions` - Get total questions count
- `getContractStats` - Get comprehensive statistics
- `getOpenQuestions` - Get open questions
- `getQuestion(1)` - Get details for question ID 1
- `getQuestionAnswers(1)` - Get answers for question ID 1
- `validate` - Get next unvalidated answer and transcribe audio
- `help` - Show available functions
- `connection` - Check network connection

### REST API
- `POST /call` - Call a function
  ```json
  {
    "function_name": "getContractStats"
  }
  ```

## Examples

### Chat Examples
- User: `getContractStats`
- Agent: `✅ Contract Statistics:
📊 Total Questions: 5
📝 Total Answers: 12
✅ Valid Answers: 8
🔓 Open Questions: 2
🔒 Closed Questions: 3`

- User: `getQuestion(1)`
- Agent: `✅ Question 1:
👤 Asker: 0x1234567890123456789012345678901234567890
❓ Prompt: What is the capital of France?
📊 Answers Needed: 3
💰 Bounty: 1000000000000000000 wei
✅ Valid Answers: 2
📝 Total Answers: 3
📈 Status: Open
🕐 Created: 1703123456
🕐 Closed: 0
📋 Exists: true`

- User: `getOpenQuestions`
- Agent: `✅ Open Questions: 1, 3, 5`

- User: `validate`
- Agent: `✅ **Validation Request for Unanswered Question**

📋 **Question Details:**
❓ Question ID: 1
❓ Prompt: "What is the capital of France?"
📊 Progress: 2/3 valid answers needed
📝 Total Answers: 3

📝 **Answer to Validate:**
👤 Provider: 0x1234567890123456789012345678901234567890
🎵 Audio Hash (Blob ID): Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24
📊 Answer Index: 0
🕐 Submitted: 1703123456

🎵 **Audio Transcription:**
✅ Transcription: The capital of France is Paris.

💡 **Next Steps:**
Use the contract's validateAnswer function to mark this answer as valid or invalid.`

### REST API Example
```bash
curl -X POST http://localhost:8003/call \
  -H "Content-Type: application/json" \
  -d '{"function_name": "getContractStats"}'
```

Response:
```json
{
  "function_name": "getContractStats",
  "result": "✅ Contract Statistics:\n📊 Total Questions: 5\n📝 Total Answers: 12\n✅ Valid Answers: 8\n🔓 Open Questions: 2\n🔒 Closed Questions: 3",
  "success": true
}
```

## Function Arguments

Some functions require arguments. Use the format `functionName(arg1,arg2,...)`:

- `getQuestion(1)` - Get question with ID 1
- `getQuestionAnswers(2)` - Get answers for question ID 2
- `getQuestionStats(3)` - Get stats for question ID 3

## Response Format

All responses follow the format: 
- ✅ Success: `✅ function_name() = result`
- ❌ Error: `❌ Error message`

## Contract Features

The AskWorld contract allows users to:
- Ask questions with bounties
- Submit audio answers
- Validate answers through AI validators
- Distribute bounties to valid answer providers

This agent provides read-only access to monitor the contract's state and activity.