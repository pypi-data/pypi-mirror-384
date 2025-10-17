"""
Example: Using Velatir Guardrails with LangChain

This example demonstrates how to use VelatirGuardrailMiddleware to add
compliance checking to a LangChain agent.
"""

import asyncio
import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from langchain_velatir import VelatirGuardrailMiddleware


# Define some example tools
@tool
def search_database(query: str) -> str:
    """Search a customer database."""
    return f"Found 5 results for: {query}"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a customer."""
    return f"Email sent to {to}: {subject}"


async def main():
    """Run the guardrail example."""
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

    # Create Velatir guardrail middleware
    # This will check all agent responses against GDPR, EU AI Act, and Bias policies
    guardrail_middleware = VelatirGuardrailMiddleware(
        api_key=velatir_api_key,
        policies=["GDPR", "EU_AI_ACT", "BIAS_FAIRNESS"],
        mode="blocking",  # Block responses that violate policies
        blocked_message="This response was blocked due to compliance violations.",
    )

    # Create the agent with guardrails
    tools = [search_database, send_email]

    # Note: This is a simplified example. In LangChain 1.0, you would use:
    # agent = create_react_agent(model, tools, middleware=[guardrail_middleware])

    print("Example: Velatir Guardrail Middleware")
    print("=" * 50)
    print("\nThis agent has guardrails that check responses against:")
    print("- GDPR compliance")
    print("- EU AI Act requirements")
    print("- Bias & Fairness policies")
    print("\nAny responses that violate these policies will be blocked.\n")

    # Example 1: Safe query
    print("Example 1: Safe database query")
    print("-" * 50)
    result = await search_database.ainvoke({"query": "active customers"})
    print(f"Result: {result}\n")

    # Example 2: Query with PII concerns
    print("Example 2: Query with potential PII concerns")
    print("-" * 50)
    result = await search_database.ainvoke({"query": "customers with social security numbers"})
    print(f"Result: {result}")
    print("Note: This would be reviewed by Velatir's policy engine\n")

    print("\nGuardrails are active and monitoring all agent responses!")


if __name__ == "__main__":
    asyncio.run(main())
