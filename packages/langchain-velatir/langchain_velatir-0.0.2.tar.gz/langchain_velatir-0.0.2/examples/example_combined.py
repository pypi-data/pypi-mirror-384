"""
Example: Combining Guardrails and Human-in-the-Loop

This example demonstrates how to use both VelatirGuardrailMiddleware and
VelatirHITLMiddleware together for comprehensive governance.
"""

import asyncio
import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain_core.tools import tool

from langchain_velatir import VelatirGuardrailMiddleware, VelatirHITLMiddleware


# Define example tools
@tool
def process_customer_data(customer_id: str, operation: str) -> str:
    """Process customer data with specified operation."""
    return f"Processed data for customer {customer_id}: {operation}"


@tool
def generate_report(report_type: str, filters: dict) -> str:
    """Generate a business report."""
    return f"Generated {report_type} report with filters: {filters}"


@tool
def execute_transaction(amount: float, account: str) -> str:
    """Execute a financial transaction."""
    return f"Executed transaction: ${amount} to {account}"


async def main():
    """Run the combined example."""
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

    # Create both middleware components
    guardrail_middleware = VelatirGuardrailMiddleware(
        api_key=velatir_api_key,
        policies=["GDPR", "EU_AI_ACT", "BIAS_FAIRNESS"],
        mode="blocking",
    )

    hitl_middleware = VelatirHITLMiddleware(
        api_key=velatir_api_key,
        polling_interval=5.0,
        timeout=600.0,
        require_approval_for=["process_customer_data", "execute_transaction"],
    )

    # Create the agent with both middleware components
    tools = [process_customer_data, generate_report, execute_transaction]

    # Note: In LangChain 1.0, you would use:
    # agent = create_react_agent(
    #     model,
    #     tools,
    #     middleware=[guardrail_middleware, hitl_middleware]
    # )

    print("Example: Combined Guardrails + Human-in-the-Loop")
    print("=" * 50)
    print("\nThis agent has:")
    print("\n1. GUARDRAILS (after_agent):")
    print("   - GDPR compliance checking")
    print("   - EU AI Act requirements")
    print("   - Bias & Fairness validation")
    print("\n2. HUMAN-IN-THE-LOOP (before_tool):")
    print("   - Approval required for customer data processing")
    print("   - Approval required for financial transactions")
    print("\n3. LAYERED PROTECTION:")
    print("   - HITL checks BEFORE tool execution")
    print("   - Guardrails check AFTER agent response")
    print("   - Complete governance coverage\n")

    # Example workflow
    print("Example Workflow:")
    print("-" * 50)

    # 1. Safe operation (no approval, passes guardrails)
    print("\n1. Generate a report (no approval needed)")
    result = await generate_report.ainvoke({
        "report_type": "sales",
        "filters": {"year": 2024}
    })
    print(f"   ✓ {result}")

    # 2. Sensitive operation (needs approval + guardrail check)
    print("\n2. Process customer data (approval required)")
    print("   → Creating review task in Velatir...")
    print("   → Waiting for human approval...")
    try:
        result = await process_customer_data.ainvoke({
            "customer_id": "CUST-001",
            "operation": "update_email"
        })
        print(f"   ✓ Approved and compliant: {result}")
    except Exception as e:
        print(f"   ✗ Blocked: {e}")

    # 3. High-risk operation (needs approval + strict guardrail)
    print("\n3. Execute transaction (approval required + guardrails)")
    print("   → Creating review task in Velatir...")
    print("   → Waiting for human approval...")
    try:
        result = await execute_transaction.ainvoke({
            "amount": 5000.0,
            "account": "ACC-123"
        })
        print(f"   ✓ Approved and compliant: {result}")
    except Exception as e:
        print(f"   ✗ Blocked: {e}")

    print("\n" + "=" * 50)
    print("Complete governance achieved!")
    print("- Human oversight for sensitive operations")
    print("- Automated compliance checking for all responses")
    print("- Audit trail in Velatir dashboard")


if __name__ == "__main__":
    asyncio.run(main())
