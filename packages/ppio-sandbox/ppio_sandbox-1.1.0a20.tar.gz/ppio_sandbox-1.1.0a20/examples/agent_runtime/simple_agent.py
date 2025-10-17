#!/usr/bin/env python3
"""
Simple Agent Example - Runtime Module

This example demonstrates how to create a simple AI agent using the PPIO Agent Runtime.
"""

import asyncio
from ppio_sandbox.agent_runtime import PPIOAgentRuntimeApp, RequestContext

# Create the agent app
app = PPIOAgentRuntimeApp(debug=True)


@app.entrypoint
async def my_agent(request: dict, context: RequestContext) -> dict:
    """Main agent logic.
    
    Args:
        request: The incoming request data
        context: Request context with metadata
        
    Returns:
        Agent response
    """
    query = request.get("query", "")
    session_id = context.session_id
    
    # Simple echo agent logic
    response = f"Echo: {query}"
    
    # You can add your AI/ML logic here
    # For example:
    # - Call LLM APIs
    # - Process data
    # - Run computations
    
    return {
        "response": response,
        "session_id": session_id,
        "request_id": context.request_id,
        "timestamp": context.timestamp.isoformat(),
        "metadata": {
            "processed_at": context.timestamp.isoformat(),
            "user_agent": context.user_agent,
        }
    }


@app.ping
def health_check() -> dict:
    """Custom health check."""
    return {
        "status": "healthy",
        "service": "Simple Echo Agent",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Run the agent server
    app.run(port=8080, host="0.0.0.0")
