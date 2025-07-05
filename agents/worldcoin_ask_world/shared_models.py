"""
Shared models for simple blockchain agent.
"""

from uagents import Model


class FunctionCallRequest(Model):
    """Request model for function calls."""
    function_name: str


class FunctionCallResponse(Model):
    """Response model for function calls."""
    function_name: str
    result: str
    success: bool
    error_message: str = None 