"""
Simple blockchain operations for reading from a specific Worldcoin Mainnet contract.
"""

import os
import json
import asyncio
import base64
import requests
from typing import Any
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables from multiple possible locations
load_dotenv("../.env")  # agents/.env
load_dotenv("../../.env")  # root .env
load_dotenv(".env")  # current directory .env

# Import configuration
try:
    from config import CONTRACT_ADDRESS, WORLDCOIN_MAINNET_RPC, WALRUS_AGENT_ADDRESS
except ImportError:
    # Fallback values if config import fails
    CONTRACT_ADDRESS = "0xbDBcB9d5f5cF6c6040A7b6151c2ABE25C68f83af"
    WORLDCOIN_MAINNET_RPC = os.getenv('WORLDCHAIN_RPC')
    WALRUS_AGENT_ADDRESS = "agent1qfxa0vgsvwcp43ykgnysqp5aj2kc90xnxrhphl2jnc34p0p7hkej2srxnsq"

# Get private key for transactions
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    print("⚠️  Warning: PRIVATE_KEY not found in environment variables. Transaction functions will not work.")
    print("   Set PRIVATE_KEY in your .env file to enable transaction functionality.")

# Load ABI from the JSON file
def load_abi():
    """Load ABI from the compiled contract JSON file."""
    try:
        # Path to the ABI file relative to the agent directory
        abi_path = "../../smart_contracts/out/AskWorld.sol/AskWorld.json"
        with open(abi_path, 'r') as f:
            contract_json = json.load(f)
            return contract_json['abi']
    except Exception as e:
        print(f"Error loading ABI: {e}")
        # Fallback to a minimal ABI with basic functions
        return [
            {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
            {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"totalQuestions","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"totalAnswers","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"totalValidAnswers","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getContractStats","outputs":[{"internalType":"uint256","name":"totalQuestionsCount","type":"uint256"},{"internalType":"uint256","name":"totalAnswersCount","type":"uint256"},{"internalType":"uint256","name":"totalValidAnswersCount","type":"uint256"},{"internalType":"uint256","name":"openQuestionsCount","type":"uint256"},{"internalType":"uint256","name":"closedQuestionsCount","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getOpenQuestions","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"questionId","type":"uint256"}],"name":"getQuestion","outputs":[{"components":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"address","name":"asker","type":"address"},{"internalType":"string","name":"prompt","type":"string"},{"internalType":"uint256","name":"answersNeeded","type":"uint256"},{"internalType":"uint256","name":"bounty","type":"uint256"},{"internalType":"uint256","name":"validAnswersCount","type":"uint256"},{"internalType":"uint256","name":"totalAnswersCount","type":"uint256"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"uint256","name":"createdAt","type":"uint256"},{"internalType":"uint256","name":"closedAt","type":"uint256"},{"internalType":"bool","name":"exists","type":"bool"}],"internalType":"struct AskWorld.Question","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"questionId","type":"uint256"}],"name":"getQuestionAnswers","outputs":[{"components":[{"internalType":"address","name":"provider","type":"address"},{"internalType":"string","name":"audioHash","type":"string"},{"internalType":"uint8","name":"status","type":"uint8"},{"internalType":"uint256","name":"submittedAt","type":"uint256"},{"internalType":"uint256","name":"validatedAt","type":"uint256"}],"internalType":"struct AskWorld.Answer[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"questionId","type":"uint256"}],"name":"getQuestionStats","outputs":[{"internalType":"uint256","name":"validCount","type":"uint256"},{"internalType":"uint256","name":"totalCount","type":"uint256"},{"internalType":"uint256","name":"neededCount","type":"uint256"},{"internalType":"bool","name":"isComplete","type":"bool"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getNextUnvalidatedAnswer","outputs":[{"internalType":"uint256","name":"questionId","type":"uint256"},{"internalType":"uint256","name":"answerIndex","type":"uint256"},{"internalType":"address","name":"provider","type":"address"},{"internalType":"string","name":"audioHash","type":"string"},{"internalType":"uint256","name":"submittedAt","type":"uint256"}],"stateMutability":"view","type":"function"}
        ]

CONTRACT_ABI = load_abi()

# Walrus agent communication for blob transcription
async def send_audio_to_voice_agent(ctx, audio_hash: str) -> str:
    """Send blob ID to Walrus agent for transcription via voice-to-text agent."""
    try:
        # Import the shared models from local shared_models
        from shared_models import BlobTranscriptionRequest, BlobTranscriptionResponse
        
        # Create request to download and transcribe the blob
        request = BlobTranscriptionRequest(
            blob_id=audio_hash,
            request_id=f"transcribe_{audio_hash}"
        )
        
        # Send request to the Walrus agent using ctx.send_and_receive
        response, status = await ctx.send_and_receive(
            WALRUS_AGENT_ADDRESS, 
            request, 
            response_type=BlobTranscriptionResponse,
            timeout=60
        )
        
        if response and hasattr(response, 'success') and response.success:
            return f"✅ Transcription: {response.transcript}"
        else:
            error_msg = getattr(response, 'error_message', 'Unknown error')
            return f"❌ Transcription failed: {error_msg}"
            
    except Exception as e:
        return f"❌ Error communicating with Walrus agent: {e}"

async def validate_transcription_with_llm(question_prompt: str, transcription: str) -> tuple[bool, str]:
    """
    Validate if the transcription is a valid answer to the question using GPT-4o.
    Returns (is_valid: bool, reason: str)
    """
    try:
        import openai
        
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return False, "OpenAI API key not found in environment variables"
        
        client = openai.AsyncOpenAI(api_key=api_key)
        
        prompt = f"""You are an AI validator for audio transcriptions. Your job is to determine if a transcribed audio answer is a valid response to a given question.

Question: "{question_prompt}"
Transcribed Answer: "{transcription}"

Please analyze if this transcription is a valid answer to the question. Consider:
1. Is it a meaningful response (not just "um", "uh", or silence)?
2. Is it relevant to the question being asked?
3. Does it provide useful information or attempt to answer the question?

Respond with ONLY "TRUE" or "FALSE" followed by a brief reason (max 100 characters).

Example responses:
- "TRUE - Provides relevant restaurant recommendation"
- "FALSE - Just says 'I don't know'"
- "FALSE - Transcription too short to be meaningful"
- "TRUE - Mentions pizza places in Rome as requested"

Your response:"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the response
        if result.upper().startswith("TRUE"):
            return True, result[5:].strip()  # Remove "TRUE - " prefix
        elif result.upper().startswith("FALSE"):
            return False, result[6:].strip()  # Remove "FALSE - " prefix
        else:
            # Fallback parsing
            return True, result
            
    except Exception as e:
        return False, f"Error during GPT-4o validation: {e}"

async def validate_answer_transaction(question_id: int, answer_index: int, is_valid: bool) -> str:
    """
    Submit a transaction to validate an answer on the blockchain.
    
    Args:
        question_id: ID of the question
        answer_index: Index of the answer within the question
        is_valid: Whether the answer is valid or not
        
    Returns:
        String with transaction result or error message
    """
    try:
        if not PRIVATE_KEY:
            return "❌ Private key not configured. Set PRIVATE_KEY in environment variables."
        
        # Create account from private key
        account = w3.eth.account.from_key(PRIVATE_KEY)
        address = account.address
        
        # Debug network information and verify we're on Worldcoin mainnet
        try:
            chain_id = w3.eth.chain_id
            print(f"🔍 Debug: Connected to chain ID: {chain_id}")
            print(f"🔍 Debug: Account address: {address}")
            
            # Verify we're on Worldcoin mainnet (chain ID 480)
            if chain_id != 480:
                return f"❌ Wrong network! Connected to chain ID {chain_id}, but need Worldcoin mainnet (chain ID 480). Please check your RPC URL."
            else:
                print(f"✅ Connected to Worldcoin mainnet (chain ID 480)")
                
        except Exception as e:
            print(f"🔍 Debug: Could not get chain ID: {e}")
            return f"❌ Failed to verify network connection: {e}"
        
        # Check if the address is an AI validator
        try:
            is_validator = contract.functions.isAIValidator(address).call()
            if not is_validator:
                return f"❌ Address {address} is not authorized as an AI validator on the contract."
        except Exception as e:
            return f"❌ Error checking AI validator status: {e}"
        
        # Build the transaction
        function_call = contract.functions.validateAnswer(question_id, answer_index, is_valid)
        
        # Estimate gas
        try:
            gas_estimate = function_call.estimate_gas({'from': address})
            gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
        except Exception as e:
            return f"❌ Gas estimation failed: {e}"
        
        # Get current gas price
        try:
            gas_price = w3.eth.gas_price
        except Exception as e:
            return f"❌ Failed to get gas price: {e}"
        
        # Get nonce - use actual account nonce but handle carefully
        try:
            nonce = w3.eth.get_transaction_count(address)
            # Ensure nonce is a proper integer
            nonce = int(nonce)
            
            # Validate nonce is reasonable
            if nonce > 1000000:  # Sanity check - if nonce is > 1M, something is wrong
                return f"❌ Nonce value too high: {nonce}. This suggests a network or account issue."
            
            print(f"🔍 Debug: Account nonce: {nonce} (type: {type(nonce)})")
            
            # Ensure nonce is a clean integer to avoid RLP encoding issues
            nonce = int(str(nonce))
            
        except Exception as e:
            return f"❌ Failed to get nonce: {e}"
        
        # SIMPLE APPROACH: Build transaction with minimal parameters
        print(f"🔧 Using simple transaction building approach")
        
        # Get the function data
        data = function_call._encode_transaction_data()
        
        # Build a simple transaction with actual nonce and chainId for EIP-155 compliance
        transaction = {
            'from': address,
            'to': CONTRACT_ADDRESS,
            'gas': int(gas_limit),
            'gasPrice': int(gas_price),
            'nonce': nonce,  # Use actual account nonce
            'data': data,
            'value': 0,
            'chainId': 480  # Worldcoin mainnet chain ID for EIP-155 compliance
        }
        
        print(f"🔍 Debug: Simple transaction built: {transaction}")
        
        # Sign and send transaction with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔧 Attempt {attempt + 1}/{max_retries} with nonce {nonce}")
                
                # Try with current nonce
                test_transaction = transaction.copy()
                test_transaction['nonce'] = nonce
                
                signed_txn = w3.eth.account.sign_transaction(test_transaction, PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                print(f"✅ Transaction sent successfully: {tx_hash.hex()}")
                break
                
            except Exception as e:
                error_str = str(e)
                print(f"❌ Attempt {attempt + 1} failed: {error_str}")
                
                if "nonce too low" in error_str.lower():
                    # Try with next nonce
                    nonce += 1
                    print(f"🔧 Retrying with nonce {nonce}")
                elif "rlp" in error_str.lower():
                    # RLP error - try with nonce 0
                    nonce = 0
                    print(f"🔧 RLP error detected, trying with nonce 0")
                elif attempt == max_retries - 1:
                    # Last attempt failed
                    return f"❌ Failed to send transaction after {max_retries} attempts: {e}\n🔍 Final transaction details: {test_transaction}"
                else:
                    # Other error - wait and retry
                    import time
                    time.sleep(1)
                    continue
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt.status == 1:
            return f"✅ Transaction successful!\n🔗 TX Hash: {tx_hash.hex()}\n📊 Gas Used: {receipt.gasUsed}\n💰 Gas Price: {receipt.effectiveGasPrice} wei\n📝 Answer marked as {'VALID' if is_valid else 'INVALID'}"
        else:
            return f"❌ Transaction failed!\n🔗 TX Hash: {tx_hash.hex()}\n📊 Gas Used: {receipt.gasUsed}"
            
    except Exception as e:
        return f"❌ Transaction error: {e}"

async def validate_unanswered_questions(ctx) -> str:
    """Validate unanswered questions by checking for answers that need validation."""
    try:
        # First, get all open questions
        open_questions = contract.functions.getOpenQuestions().call()
        
        if not open_questions:
            return "✅ No open questions found to validate."
        
        # Get the next unvalidated answer
        try:
            unvalidated_result = contract.functions.getNextUnvalidatedAnswer().call()
            question_id, answer_index, provider, audio_hash, submitted_at = unvalidated_result
            
            # Debug: Print the values to see what we got
            print(f"🔍 Debug: question_id={question_id}, answer_index={answer_index}, provider={provider}, audio_hash={audio_hash}, submitted_at={submitted_at}")
            
            if question_id == 0:
                return "✅ No unvalidated answers found."
            
        except Exception as e:
            # Check if this is the specific "No unvalidated answers found" revert
            error_str = str(e)
            if "No unvalidated answers found" in error_str or "0x08c379a0" in error_str:
                return "✅ No unvalidated answers found to validate."
            else:
                # Re-raise other errors
                raise e
        
        # Get question details for context
        question_result = contract.functions.getQuestion(question_id).call()
        question_prompt = question_result[2]  # prompt is at index 2
        answers_needed = question_result[3]   # answers needed
        valid_answers = question_result[5]    # current valid answers
        total_answers = question_result[6]    # total answers
        
        # Send audio to voice-to-text agent
        transcription_result = await send_audio_to_voice_agent(ctx, audio_hash)
        # Clean up transcription_result to extract just the text (remove emoji and prefix)
        transcription_result_clean = transcription_result
        if transcription_result.startswith("✅ Transcription: "):
            transcription_result_clean = transcription_result.replace("✅ Transcription: ", "").strip()
        elif transcription_result.startswith("❌"):
            transcription_result_clean = ""
        llm_valid, llm_reason = await validate_transcription_with_llm(question_prompt, transcription_result_clean)
        
        # Format the LLM validation result with better styling
        if llm_valid:
            llm_result_text = f"""
🤖 **AI Validation Result:**
✅ **Valid Answer** - {llm_reason}"""
        else:
            llm_result_text = f"""
🤖 **AI Validation Result:**
❌ **Invalid Answer** - {llm_reason}"""

        result_text = f"""✅ **Validation Request for Unanswered Question**

📋 **Question Details:**
❓ Question ID: {question_id}
❓ Prompt: "{question_prompt}"
📊 Progress: {valid_answers}/{answers_needed} valid answers needed
📝 Total Answers: {total_answers}

📝 **Answer to Validate:**
👤 Provider: {provider}
🎵 Blob ID: {audio_hash}
📊 Answer Index: {answer_index}
🕐 Submitted: {submitted_at}

🎵 **Audio Transcription:**
{transcription_result_clean}
{llm_result_text}"""
        
        # Submit transaction to blockchain
        transaction_result = await validate_answer_transaction(question_id, answer_index, llm_valid)
        
        result_text += f"""

🔗 **Blockchain Transaction:**
{transaction_result}"""
        
        return result_text
        
    except Exception as e:
        return f"❌ Error in validation process: {e}"

async def validate_specific_answer(ctx, question_id: int, answer_index: int) -> str:
    """Validate a specific answer by question ID and answer index."""
    try:
        # Get question details
        question_result = contract.functions.getQuestion(question_id).call()
        question_prompt = question_result[2]  # prompt is at index 2
        answers_needed = question_result[3]   # answers needed
        valid_answers = question_result[5]    # current valid answers
        total_answers = question_result[6]    # total answers
        
        # Get all answers for this question
        all_answers = contract.functions.getQuestionAnswers(question_id).call()
        
        if answer_index >= len(all_answers):
            return f"❌ Answer index {answer_index} not found. Question {question_id} has {len(all_answers)} answers."
        
        # Get the specific answer
        answer = all_answers[answer_index]
        provider = answer[0]
        audio_hash = answer[1]
        status = answer[2]
        submitted_at = answer[3]
        
        # Check if answer is already validated
        status_map = {0: "Pending", 1: "Valid", 2: "Invalid"}
        status_text = status_map.get(status, "Unknown")
        
        # Send audio to voice-to-text agent
        transcription_result = await send_audio_to_voice_agent(ctx, audio_hash)
        
        # Clean up transcription_result to extract just the text
        transcription_result_clean = transcription_result
        if transcription_result.startswith("✅ Transcription: "):
            transcription_result_clean = transcription_result.replace("✅ Transcription: ", "").strip()
        elif transcription_result.startswith("❌"):
            transcription_result_clean = ""
        
        llm_valid, llm_reason = await validate_transcription_with_llm(question_prompt, transcription_result_clean)
        
        # Format the LLM validation result with better styling
        if llm_valid:
            llm_result_text = f"""
🤖 **AI Validation Result:**
✅ **Valid Answer** - {llm_reason}"""
        else:
            llm_result_text = f"""
🤖 **AI Validation Result:**
❌ **Invalid Answer** - {llm_reason}"""

        result_text = f"""✅ **Validation Request for Specific Answer**

📋 **Question Details:**
❓ Question ID: {question_id}
❓ Prompt: "{question_prompt}"
📊 Progress: {valid_answers}/{answers_needed} valid answers needed
📝 Total Answers: {total_answers}

📝 **Answer to Validate:**
👤 Provider: {provider}
🎵 Audio Hash (Blob ID): {audio_hash}
📊 Answer Index: {answer_index}
📊 Current Status: {status_text}
🕐 Submitted: {submitted_at}

🎵 **Audio Transcription:**
{transcription_result_clean}
{llm_result_text}"""
        
        return result_text
        
    except Exception as e:
        return f"❌ Error in validation process: {e}"

async def summarize_valid_answers(ctx, question_id: int) -> str:
    """Summarize all valid answers for a specific question using GPT-4o."""
    try:
        # Get question details
        question_result = contract.functions.getQuestion(question_id).call()
        question_prompt = question_result[2]  # prompt is at index 2
        answers_needed = question_result[3]   # answers needed
        valid_answers = question_result[5]    # current valid answers
        total_answers = question_result[6]    # total answers
        
        # Get all answers for this question
        all_answers = contract.functions.getQuestionAnswers(question_id).call()
        
        # Filter for valid answers (status = 1)
        valid_answer_indices = []
        for i, answer in enumerate(all_answers):
            if answer[2] == 2:  # status is Valid
                valid_answer_indices.append(i)
        
        if not valid_answer_indices:
            return f"❌ No valid answers found for question {question_id}"
        
        # Transcribe all valid answers
        transcriptions = []
        for answer_index in valid_answer_indices:
            answer = all_answers[answer_index]
            audio_hash = answer[1]
            provider = answer[0]
            
            # Send audio to voice-to-text agent
            transcription_result = await send_audio_to_voice_agent(ctx, audio_hash)
            
            # Clean up transcription_result
            transcription_clean = transcription_result
            if transcription_result.startswith("✅ Transcription: "):
                transcription_clean = transcription_result.replace("✅ Transcription: ", "").strip()
            elif transcription_result.startswith("❌"):
                transcription_clean = "Transcription failed"
            
            transcriptions.append(f"Answer {answer_index} (Provider: {provider}): {transcription_clean}")
        
        # Use GPT-4o to create a summary
        summary = await create_summary_with_gpt4o(question_prompt, transcriptions)
        
        result_text = f"""📊 **Summary of Valid Answers for Question {question_id}**

❓ **Question:** "{question_prompt}"
📊 **Valid Answers:** {len(valid_answer_indices)}/{answers_needed} needed
📝 **Total Answers:** {total_answers}

🎵 **Individual Transcriptions:**
{chr(10).join(transcriptions)}

🤖 **AI Summary:**
{summary}"""
        
        return result_text
        
    except Exception as e:
        return f"❌ Error in summarization process: {e}"


async def create_summary_with_gpt4o(question: str, transcriptions: list) -> str:
    """Create a summary of transcriptions using GPT-4o."""
    try:
        import openai
        
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "OpenAI API key not found in environment variables"
        
        client = openai.AsyncOpenAI(api_key=api_key)
        
        # Format transcriptions for the prompt
        transcriptions_text = "\n".join([f"{i+1}. {trans}" for i, trans in enumerate(transcriptions)])
        
        prompt = f"""You are an AI assistant tasked with summarizing multiple audio transcriptions that answer the same question.

Question: "{question}"

Transcriptions:
{transcriptions_text}

Please create a comprehensive summary that:
1. Identifies the main themes and common points across all answers
2. Highlights any unique or different perspectives
3. Provides a clear, organized summary of the collective wisdom
4. Keeps the summary concise but informative (max 200 words)

Your summary:"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error creating summary: {e}"

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(WORLDCOIN_MAINNET_RPC))

# Initialize contract
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# Available read functions (view functions only)
READ_FUNCTIONS = [
    "owner",
    "totalQuestions",
    "totalAnswers", 
    "totalValidAnswers",
    "getContractStats",
    "getOpenQuestions",
    "getQuestion",
    "getQuestionAnswers",
    "getQuestionStats",
    "getNextUnvalidatedAnswer"
]


def check_connection() -> str:
    """Check if we can connect to the Worldcoin Mainnet network."""
    try:
        if w3.is_connected():
            latest_block = w3.eth.block_number
            return f"✅ Connected to Worldcoin Mainnet!\n📊 Latest block: {latest_block}\n🔗 Contract: {CONTRACT_ADDRESS}"
        else:
            return f"❌ Failed to connect to Worldcoin Mainnet at {WORLDCOIN_MAINNET_RPC}"
    except Exception as e:
        return f"❌ Connection error: {e}"


async def read_function(function_name: str, *args) -> str:
    """
    Read a specific function from the contract.
    
    Args:
        function_name: Name of the function to call
        *args: Arguments to pass to the function
        
    Returns:
        String with the result or error message
    """
    try:
        # Check if function exists and is readable
        if function_name not in READ_FUNCTIONS:
            return f"❌ Function '{function_name}' not found or not readable.\n📋 Available functions: {', '.join(READ_FUNCTIONS)}"
        
        # Call the function with arguments if provided
        if args:
            result = getattr(contract.functions, function_name)(*args).call()
        else:
            result = getattr(contract.functions, function_name)().call()
        
        # Format the result based on the function
        if function_name == "getContractStats":
            total_questions, total_answers, total_valid, open_questions, closed_questions = result
            return f"✅ Contract Statistics:\n📊 Total Questions: {total_questions}\n📝 Total Answers: {total_answers}\n✅ Valid Answers: {total_valid}\n🔓 Open Questions: {open_questions}\n🔒 Closed Questions: {closed_questions}"
        
        elif function_name == "getQuestion":
            question = result
            status_map = {0: "Open", 1: "Closed"}
            return f"✅ Question {question[0]}:\n👤 Asker: {question[1]}\n❓ Prompt: {question[2]}\n📊 Answers Needed: {question[3]}\n💰 Bounty: {question[4]} wei\n✅ Valid Answers: {question[5]}\n📝 Total Answers: {question[6]}\n📈 Status: {status_map.get(question[7], 'Unknown')}\n🕐 Created: {question[8]}\n🕐 Closed: {question[9]}\n📋 Exists: {question[10]}"
        
        elif function_name == "getQuestionAnswers":
            answers = result
            if not answers:
                return f"✅ No answers found for this question"
            
            answer_list = []
            for i, answer in enumerate(answers):
                status_map = {0: "Pending", 1: "Valid", 2: "Invalid"}
                answer_list.append(f"Answer {i}:\n👤 Provider: {answer[0]}\n🎵 Audio Hash: {answer[1]}\n📊 Status: {status_map.get(answer[2], 'Unknown')}\n🕐 Submitted: {answer[3]}\n🕐 Validated: {answer[4]}")
            
            return f"✅ Question Answers:\n" + "\n\n".join(answer_list)
        
        elif function_name == "getQuestionStats":
            valid_count, total_count, needed_count, is_complete = result
            return f"✅ Question Statistics:\n✅ Valid Answers: {valid_count}\n📝 Total Answers: {total_count}\n📊 Answers Needed: {needed_count}\n🎯 Complete: {is_complete}"
        
        elif function_name == "getNextUnvalidatedAnswer":
            question_id, answer_index, provider, audio_hash, submitted_at = result
            if question_id == 0:
                return f"✅ No unvalidated answers found"
            return f"✅ Next Unvalidated Answer:\n❓ Question ID: {question_id}\n📝 Answer Index: {answer_index}\n👤 Provider: {provider}\n🎵 Audio Hash: {audio_hash}\n🕐 Submitted: {submitted_at}"
        

        
        elif function_name == "getOpenQuestions":
            open_questions = result
            if not open_questions:
                return f"✅ No open questions found"
            return f"✅ Open Questions: {', '.join(map(str, open_questions))}"
        
        # Format simple results
        elif isinstance(result, bool):
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


async def handle_blockchain_request(ctx, function_name: str, *args) -> str:
    """
    Handle blockchain requests.
    
    Args:
        function_name: Name of the function to call
        *args: Arguments to pass to the function
        
    Returns:
        String with the result
    """
    function_name = function_name.strip()
    
    if function_name.lower() in ["connection", "connect", "network", "status"]:
        return check_connection()
    
    elif function_name.lower() in ["help", "functions", "list"]:
        return get_available_functions()
    
    elif function_name.lower().startswith("validate "):
        parts = function_name.lower().split()
        if len(parts) == 2 and parts[1] == "next":
            return await validate_unanswered_questions(ctx)
        elif len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            question_id = int(parts[1])
            answer_index = int(parts[2])
            return await validate_specific_answer(ctx, question_id, answer_index)
        else:
            return "❌ Invalid validate command. Use 'validate next' or 'validate <question_id> <answer_index>'"
    
    elif function_name.lower().startswith("summarize valid "):
        parts = function_name.lower().split()
        if len(parts) == 3 and parts[1] == "valid" and parts[2].isdigit():
            question_id = int(parts[2])
            return await summarize_valid_answers(ctx, question_id)
        else:
            return "❌ Invalid summarize command. Use 'summarize valid <question_id>'"
    
    else:
        return await read_function(function_name, *args) 