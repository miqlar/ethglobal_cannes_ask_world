"""
Simple Blockchain Agent for reading Worldcoin Mainnet contract.
"""

from uagents import Agent
from chat_proto import chat_proto
from shared_models import FunctionCallRequest, FunctionCallResponse

# Configure agent for mailbox mode
SEED_PHRASE = "put_your_seed_phrase_here"

agent = Agent(
    name="blockchain-simple",
    port=8003,  # Using 8003 to avoid conflicts with other agents
    #endpoint=["http://localhost:8003/submit"],
    mailbox=True
)

# Include chat protocol and publish manifest so ASI:One / Agentverse can find it
agent.include(chat_proto, publish_manifest=True)

# Add REST endpoint for direct testing
@agent.on_rest_post("/call", FunctionCallRequest, FunctionCallResponse)
async def handle_function_call_rest(ctx, req: FunctionCallRequest) -> FunctionCallResponse:
    """REST endpoint for function calls."""
    ctx.logger.info(f"Received REST function call request: {req.function_name}")
    
    try:
        from blockchain_operations import handle_blockchain_request
        
        # Parse arguments if provided in the function name
        # Format: function_name(arg1,arg2,...)
        if '(' in req.function_name and req.function_name.endswith(')'):
            func_name = req.function_name.split('(')[0]
            args_str = req.function_name.split('(')[1].rstrip(')')
            
            # Parse arguments
            args = []
            if args_str:
                for arg in args_str.split(','):
                    arg = arg.strip()
                    # Try to convert to int if it's a number
                    try:
                        if arg.startswith('0x'):
                            args.append(int(arg, 16))
                        else:
                            args.append(int(arg))
                    except ValueError:
                        args.append(arg)
            
            result = await handle_blockchain_request(func_name, *args)
        else:
            result = await handle_blockchain_request(req.function_name)
        
        if result.startswith("✅"):
            return FunctionCallResponse(
                function_name=req.function_name,
                result=result,
                success=True
            )
        else:
            return FunctionCallResponse(
                function_name=req.function_name,
                result="",
                success=False,
                error_message=result
            )
        
    except Exception as exc:
        ctx.logger.error(f"Function call failed: {exc}")
        return FunctionCallResponse(
            function_name=req.function_name,
            result="",
            success=False,
            error_message=str(exc)
        )

# Copy the address shown below
print(f"Your agent's address is: {agent.address}")

if __name__ == "__main__":
    agent.run() 