# Simple Blockchain Agent - Worldcoin Mainnet AskWorld Reader

A simple uAgent that reads from and writes to the AskWorld smart contract on the Worldcoin Mainnet blockchain.

## Contract Details

- **Address**: `0x185591a5DC4B65B8B7AF5befca02C702F23C476C`
- **Network**: Worldcoin Mainnet
- **RPC**: https://worldchain-mainnet.g.alchemy.com/public
- **Contract**: AskWorld - A smart contract for managing questions with audio answers and AI validation

## Features

### Read Operations
- Query contract statistics and question/answer data
- Get detailed information about questions and answers
- Monitor contract activity

### Write Operations (Transaction Support)
- **AI-Powered Answer Validation**: Automatically transcribe audio answers and validate them using GPT-4o
- **Blockchain Transactions**: Submit validation results to the smart contract
- **Gas Estimation**: Automatic gas estimation and transaction signing
- **Validator Authorization**: Check if the agent's address is authorized as an AI validator

## Available Functions

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

### Answer Validation (with Transaction Support)
- `getNextUnvalidatedAnswer` - Get the next answer that needs validation
- `validate next` - **NEW**: Process the next unanswered question, transcribe audio, validate with GPT-4o, and submit transaction to blockchain
- `validate <question_id> <answer_index>` - Validate a specific answer, transcribe audio, validate with GPT-4o (read-only, no transaction)
- `summarize valid <question_id>` - Summarize all valid answers for a question using GPT-4o

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. **Configure Private Key** (Required for transactions):
   Create a `.env` file in the agent directory with:
   ```
   PRIVATE_KEY=your_private_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   **Important**: 
   - The private key must correspond to an address that is authorized as an AI validator on the contract
   - Never commit your private key to version control
   - The agent will check if your address is authorized before submitting transactions

3. Run the agent:
```bash
python agent.py
```

## Usage

### Chat Interface

#### Read Operations
- `owner` - Get contract owner
- `totalQuestions` - Get total questions count
- `getContractStats` - Get comprehensive statistics
- `getOpenQuestions` - Get open questions
- `getQuestion(1)` - Get details for question ID 1
- `getQuestionAnswers(1)` - Get answers for question ID 1
- `help` - Show available functions
- `connection` - Check network connection

#### Write Operations (Transactions)
- `validate next` - **Process and validate the next unvalidated answer (submits transaction)**
- `validate 1 0` - **Validate answer index 0 of question 1 (read-only, no transaction)**
- `summarize valid 1` - Summarize all valid answers for question 1

### REST API
- `POST /call` - Call a function
  ```json
  {
    "function_name": "getContractStats"
  }
  ```

## Examples

### Chat Examples

#### Read Operations
- User: `getContractStats`
- Agent: `✅ Contract Statistics:
📊 Total Questions: 5
📝 Total Answers: 12
✅ Valid Answers: 8
🔓 Open Questions: 2
🔒 Closed Questions: 3`

#### Write Operations (Transactions)
- User: `validate next`
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

🤖 **AI Validation Result:**
✅ **Valid Answer** - Provides correct capital city information

🔗 **Blockchain Transaction:**
✅ Transaction successful!
🔗 TX Hash: 0x1234567890abcdef...
📊 Gas Used: 150000
💰 Gas Price: 20000000000 wei
✅ Answer marked as VALID`

- User: `validate 1 0`
- Agent: `✅ **Validation Request for Specific Answer**

📋 **Question Details:**
❓ Question ID: 1
❓ Prompt: "What is the capital of France?"
📊 Progress: 2/3 valid answers needed
📝 Total Answers: 3

📝 **Answer to Validate:**
👤 Provider: 0x1234567890123456789012345678901234567890
🎵 Audio Hash (Blob ID): Y3XBOEfW77JAon9Kl-pRDy0kRWTgqjxzjYEv0yMfO24
📊 Answer Index: 0
📊 Current Status: Pending
🕐 Submitted: 1703123456

🎵 **Audio Transcription:**
✅ Transcription: The capital of France is Paris.

🤖 **AI Validation Result:**
✅ **Valid Answer** - Provides correct capital city information

💡 **Note:** This is a read-only validation. Use 'validate next' to submit transactions to the blockchain.`

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

## Transaction Process

When you run `validate next`, the agent:

1. **Fetches Answer Data**: Gets the audio blob ID and question details from the blockchain
2. **Transcribes Audio**: Sends the blob ID to the Walrus agent for transcription via voice-to-text
3. **AI Validation**: Uses GPT-4o to determine if the transcription is a valid answer
4. **Authorization Check**: Verifies that the agent's address is authorized as an AI validator
5. **Gas Estimation**: Estimates gas requirements for the transaction
6. **Transaction Submission**: Signs and submits the transaction to the blockchain
7. **Confirmation**: Waits for transaction confirmation and reports the result

## Security Considerations

- **Private Key Security**: Keep your private key secure and never share it
- **Validator Authorization**: Only addresses authorized as AI validators can submit validation transactions
- **Gas Costs**: Transactions require gas fees paid in the native token
- **Network Security**: Ensure you're connected to the correct Worldcoin Mainnet

## Function Arguments

Some functions require arguments. Use the format `functionName(arg1,arg2,...)`:

- `getQuestion(1)` - Get question with ID 1
- `getQuestionAnswers(2)` - Get answers for question ID 2
- `getQuestionStats(3)` - Get stats for question ID 3
- `validate 1 0` - Validate answer index 0 of question 1 (read-only, no transaction)

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

This agent provides both read access to monitor the contract's state and write access to validate answers through AI-powered analysis and blockchain transactions.