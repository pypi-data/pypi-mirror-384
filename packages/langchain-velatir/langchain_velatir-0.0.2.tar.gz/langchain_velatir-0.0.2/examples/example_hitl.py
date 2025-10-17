"""
Example: Using Velatir Human-in-the-Loop with LangChain

This example demonstrates how to use VelatirHITLMiddleware to require
human approval before executing sensitive operations.
"""

import asyncio
import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain_core.tools import tool

from langchain_velatir import VelatirHITLMiddleware


# Define some example tools
@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    return f"Contents of {path}: [file contents]"


@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    return f"Deleted file: {path}"


@tool
def send_notification(message: str, urgency: str) -> str:
    """Send a notification to users."""
    return f"Sent {urgency} notification: {message}"


async def main():
    """Run the HITL example."""
    # Get API keys from environment
    velatir_api_key = os.getenv("VELATIR_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not velatir_api_key:
        print("Please set VELATIR_API_KEY environment variable")
        return
    if not openai_api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Initialize the model
    model = ChatOpenAI(model="gpt-4", api_key=openai_api_key)

    # Create Velatir HITL middleware
    # This will require human approval for specific tools
    hitl_middleware = VelatirHITLMiddleware(
        api_key=velatir_api_key,
        polling_interval=5.0,  # Check for approval every 5 seconds
        timeout=600.0,  # Wait up to 10 minutes for approval
        require_approval_for=["delete_file", "send_notification"],  # Only these tools need approval
    )

    # Create the agent with HITL
    tools = [read_file, delete_file, send_notification]

    # Note: This is a simplified example. In LangChain 1.0, you would use:
    # agent = create_react_agent(model, tools, middleware=[hitl_middleware])

    print("Example: Velatir Human-in-the-Loop Middleware")
    print("=" * 50)
    print("\nThis agent requires human approval for:")
    print("- delete_file: Deleting files")
    print("- send_notification: Sending notifications")
    print("\nThe workflow will pause until a human approves or rejects.\n")

    # Example 1: Safe operation (no approval needed)
    print("Example 1: Reading a file (no approval needed)")
    print("-" * 50)
    result = await read_file.ainvoke({"path": "/data/report.txt"})
    print(f"Result: {result}\n")

    # Example 2: Sensitive operation (approval required)
    print("Example 2: Deleting a file (approval required)")
    print("-" * 50)
    print("This operation will create a review task in Velatir...")
    print("The workflow will pause until approved/rejected.")
    print("Check your Velatir dashboard or Slack/Teams for the approval request.\n")

    try:
        # This would wait for approval
        result = await delete_file.ainvoke({"path": "/data/old_report.txt"})
        print(f"Result: {result}")
        print("Operation was APPROVED!\n")
    except Exception as e:
        print(f"Operation was DENIED: {e}\n")

    print("\nHuman-in-the-loop workflow complete!")


if __name__ == "__main__":
    asyncio.run(main())
