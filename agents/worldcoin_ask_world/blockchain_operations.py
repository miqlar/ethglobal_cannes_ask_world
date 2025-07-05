"""
Simple blockchain operations for reading from a specific Worldcoin Mainnet contract.
"""

import os
import json
import asyncio
import base64
from typing import Any
from dotenv import load_dotenv
from web3 import Web3

load_dotenv("../.env")

# Import configuration
try:
    from config import CONTRACT_ADDRESS, WORLDCOIN_MAINNET_RPC, WALRUS_AGENT_ADDRESS
except ImportError:
    # Fallback values if config import fails
    CONTRACT_ADDRESS = "0x185591a5DC4B65B8B7AF5befca02C702F23C476C"
    WORLDCOIN_MAINNET_RPC = "https://worldchain-mainnet.g.alchemy.com/public"
    WALRUS_AGENT_ADDRESS = "agent1qfxa0vgsvwcp43ykgnysqp5aj2kc90xnxrhphl2jnc34p0p7hkej2srxnsq"

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
        
        result_text = f"""✅ **Validation Request for Unanswered Question**

📋 **Question Details:**
❓ Question ID: {question_id}
❓ Prompt: "{question_prompt}"
📊 Progress: {valid_answers}/{answers_needed} valid answers needed
📝 Total Answers: {total_answers}

📝 **Answer to Validate:**
👤 Provider: {provider}
🎵 Audio Hash (Blob ID): {audio_hash}
📊 Answer Index: {answer_index}
🕐 Submitted: {submitted_at}

🎵 **Audio Transcription:**
{transcription_result}

💡 **Next Steps:**
Use the contract's validateAnswer function to mark this answer as valid or invalid."""
        
        return result_text
        
    except Exception as e:
        return f"❌ Error in validation process: {e}"

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
    
    elif function_name.lower() == "validate":
        return await validate_unanswered_questions(ctx)
    
    else:
        return await read_function(function_name, *args) 