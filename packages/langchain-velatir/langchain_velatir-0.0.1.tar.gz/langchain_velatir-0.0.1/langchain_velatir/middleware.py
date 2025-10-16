"""LangChain middleware implementations for Velatir integration."""

from typing import Any, Optional

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig

from langchain_velatir.client import VelatirClient
from langchain_velatir.exceptions import (
    VelatirApprovalDeniedError,
    VelatirTimeoutError,
)
from langchain_velatir.types import GuardrailMode

# Type alias for agent state (used as a dictionary)
AgentState = dict[str, Any]


# Import AgentMiddleware and hook_config from langchain
try:
    from langchain.agents import AgentMiddleware, hook_config
except ImportError:
    # Fallback for different LangChain versions
    try:
        from langchain_core.agents import AgentMiddleware, hook_config
    except ImportError:
        # Define placeholder for type hints if not available
        class AgentMiddleware:  # type: ignore
            """Placeholder for AgentMiddleware base class."""

            pass

        def hook_config(**kwargs):  # type: ignore
            """Placeholder for hook_config decorator."""

            def decorator(func):
                return func

            return decorator


class Runtime:
    """Placeholder for Runtime type if not available in imports."""

    pass


class VelatirGuardrailMiddleware(AgentMiddleware):
    """
    Guardrail middleware that validates agent responses through Velatir's policy engine.

    This middleware follows the pattern of LangChain's SafetyGuardrailMiddleware,
    but sends responses to Velatir for policy evaluation. Velatir's backend automatically
    evaluates against configured policies (GDPR, EU AI Act, Bias & Fairness, etc.) and
    determines if human intervention is required.

    The middleware runs after the agent generates a response and sends it to Velatir.
    Velatir evaluates the response through your configured flows and policies in the
    dashboard, then returns a decision (approved/denied/requires intervention).

    Example:
        ```python
        from langchain_velatir import VelatirGuardrailMiddleware

        # Policies are configured in Velatir dashboard, not in code
        middleware = VelatirGuardrailMiddleware(
            api_key="your-api-key",
            mode="blocking",  # Block if Velatir denies the response
        )

        # Add to your agent
        agent = create_react_agent(model, tools, middleware=[middleware])
        ```
    """

    def __init__(
        self,
        api_key: str,
        mode: GuardrailMode | str = GuardrailMode.BLOCKING,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        approval_timeout: float = 30.0,
        polling_interval: float = 2.0,
        blocked_message: str = "This response requires review and was not approved.",
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the Velatir guardrail middleware.

        Args:
            api_key: Velatir API key
            mode: "blocking" to block denied responses, "logging" to only log
            base_url: Optional custom Velatir API URL
            timeout: Request timeout in seconds
            approval_timeout: Max seconds to wait for Velatir decision
            polling_interval: Seconds between polling for decision
            blocked_message: Message to return when a response is blocked
            metadata: Optional metadata to include with all review tasks
        """
        super().__init__()
        self.velatir_client = VelatirClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

        self.mode = GuardrailMode(mode) if isinstance(mode, str) else mode
        self.approval_timeout = approval_timeout
        self.polling_interval = polling_interval
        self.blocked_message = blocked_message
        self.metadata = metadata or {}

    @hook_config(can_jump_to=["end"])
    async def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        """
        Hook that runs after the agent generates a response.

        Sends the response to Velatir for evaluation. Velatir's backend automatically
        evaluates the response against your configured policies and flows, determines
        risk level, and decides if human intervention is needed.

        Args:
            state: Current agent state with messages
            runtime: Agent runtime context

        Returns:
            Modified state to block the response, or None to continue
        """
        # Get the last message from the agent
        messages = state.get("messages", [])
        if not messages:
            return None

        last_message = messages[-1]

        # Only check AIMessage responses
        if not isinstance(last_message, AIMessage):
            return None

        # Extract message content for review
        content = last_message.content if hasattr(last_message, "content") else str(last_message)

        # Create a review task in Velatir
        # Velatir's backend will determine which policies apply, risk level, and routing
        try:
            # Combine provided metadata with middleware identifier
            task_metadata = {
                **self.metadata,
                "middleware": "VelatirGuardrailMiddleware",
                "mode": self.mode.value,
            }

            response = await self.velatir_client.create_review_task(
                function_name="agent_response",
                args={
                    "response": content,
                    "conversation_context": [str(m) for m in messages[-3:]],  # Last 3 messages
                },
                doc="LangChain agent response requiring governance review",
                metadata=task_metadata,
            )

            # Check the immediate response state
            if response.is_approved:
                # Velatir approved immediately (low risk, no policies triggered)
                return None

            elif response.is_denied or response.is_change_requested:
                # Velatir denied (policy violation or human rejected)
                if self.mode == GuardrailMode.BLOCKING:
                    # Block the response
                    return {
                        "messages": messages[:-1]
                        + [
                            AIMessage(
                                content=self.blocked_message,
                                additional_kwargs={
                                    "velatir_blocked": True,
                                    "review_task_id": response.review_task_id,
                                    "reason": response.requested_change,
                                },
                            )
                        ]
                    }
                else:
                    # Logging mode: add warning but don't block
                    if hasattr(last_message, "additional_kwargs"):
                        last_message.additional_kwargs["velatir_warning"] = {
                            "review_task_id": response.review_task_id,
                            "reason": response.requested_change,
                        }
                    return None

            else:
                # Pending or RequiresIntervention - wait for Velatir's decision
                try:
                    final_response = await self.velatir_client.wait_for_approval(
                        review_task_id=response.review_task_id,
                        polling_interval=self.polling_interval,
                        timeout=self.approval_timeout,
                    )

                    if final_response.is_approved:
                        # Human approved
                        return None

                    elif final_response.is_denied or final_response.is_change_requested:
                        # Human denied or requested changes
                        if self.mode == GuardrailMode.BLOCKING:
                            return {
                                "messages": messages[:-1]
                                + [
                                    AIMessage(
                                        content=self.blocked_message,
                                        additional_kwargs={
                                            "velatir_blocked": True,
                                            "review_task_id": final_response.review_task_id,
                                            "reason": final_response.requested_change,
                                        },
                                    )
                                ]
                            }
                    return None

                except VelatirTimeoutError:
                    # Timeout waiting for approval
                    if self.mode == GuardrailMode.BLOCKING:
                        return {
                            "messages": messages[:-1]
                            + [
                                AIMessage(
                                    content="Response review timed out.",
                                    additional_kwargs={
                                        "velatir_blocked": True,
                                        "review_task_id": response.review_task_id,
                                        "reason": "Timeout waiting for approval",
                                    },
                                )
                            ]
                        }
                    return None

        except Exception as e:
            # On error, behavior depends on mode
            if self.mode == GuardrailMode.BLOCKING:
                return {
                    "messages": messages[:-1]
                    + [
                        AIMessage(
                            content="Response blocked due to review system error.",
                            additional_kwargs={
                                "velatir_blocked": True,
                                "error": str(e),
                            },
                        )
                    ]
                }
            return None


class VelatirHITLMiddleware(AgentMiddleware):
    """
    Human-in-the-loop middleware for agent tool calls.

    This middleware intercepts agent tool calls and sends them to Velatir for evaluation.
    Velatir's backend automatically evaluates each tool call against your configured
    policies and flows, determines risk level, and routes to appropriate reviewers if
    human intervention is needed.

    The workflow pauses until Velatir returns a decision (which may be instant approval
    for low-risk actions, or require human review for sensitive operations).

    Example:
        ```python
        from langchain_velatir import VelatirHITLMiddleware

        # Flows and policies configured in Velatir dashboard
        middleware = VelatirHITLMiddleware(
            api_key="your-api-key",
            polling_interval=5.0,
            timeout=600.0,  # 10 minutes max wait for approval
        )

        # Optionally filter which tools to send through Velatir
        # If not specified, all tools are sent to Velatir for evaluation
        middleware = VelatirHITLMiddleware(
            api_key="your-api-key",
            require_approval_for=["delete_user", "execute_payment"],
        )

        # Add to your agent
        agent = create_react_agent(model, tools, middleware=[middleware])
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        polling_interval: float = 5.0,
        timeout: float = 600.0,
        require_approval_for: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the Velatir HITL middleware.

        Args:
            api_key: Velatir API key
            base_url: Optional custom Velatir API URL
            polling_interval: Seconds between polling for approval
            timeout: Maximum seconds to wait for approval
            require_approval_for: Optional list of tool names to send through Velatir.
                                 If None, all tools are sent to Velatir for evaluation.
            metadata: Optional metadata to include with all review tasks
        """
        super().__init__()
        self.velatir_client = VelatirClient(
            api_key=api_key,
            base_url=base_url,
        )
        self.polling_interval = polling_interval
        self.timeout = timeout
        self.require_approval_for = require_approval_for
        self.metadata = metadata or {}

    @hook_config(can_jump_to=["end"])
    async def modify_model_request(
        self, state: AgentState, runtime: Runtime, config: RunnableConfig
    ) -> dict[str, Any] | None:
        """
        Hook that runs before tool execution.

        Intercepts tool calls and sends them to Velatir for evaluation. Velatir's
        backend determines if the tool call requires human approval based on your
        configured flows and policies. Low-risk tools may be approved instantly,
        while sensitive operations are routed to human reviewers.

        Args:
            state: Current agent state
            runtime: Agent runtime context
            config: Runnable configuration

        Returns:
            Modified state or None
        """
        # Extract tool calls if any
        messages = state.get("messages", [])
        if not messages:
            return None

        last_message = messages[-1]

        # Check if there are tool calls to evaluate
        tool_calls = getattr(last_message, "tool_calls", None)
        if not tool_calls:
            return None

        # Filter tool calls based on require_approval_for setting
        if self.require_approval_for is not None:
            tool_calls = [tc for tc in tool_calls if tc.get("name") in self.require_approval_for]

        if not tool_calls:
            return None

        # Send each tool call to Velatir for evaluation
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "unknown_tool")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "unknown_id")

            try:
                # Combine provided metadata with tool call info
                task_metadata = {
                    **self.metadata,
                    "tool_call_id": tool_id,
                    "middleware": "VelatirHITLMiddleware",
                    "conversation_context": [str(m) for m in messages[-3:]],  # Last 3 messages
                }

                # Create review task - Velatir decides routing, approval requirements, etc.
                response = await self.velatir_client.create_review_task(
                    function_name=tool_name,
                    args=tool_args,
                    doc=f"LangChain agent requesting to execute: {tool_name}",
                    llm_explanation="Tool call from LangChain agent workflow",
                    metadata=task_metadata,
                )

                # Check immediate response
                if response.is_approved:
                    # Velatir approved immediately (low risk, no intervention needed)
                    continue

                # Wait for Velatir's decision (may involve human review)
                final_response = await self.velatir_client.wait_for_approval(
                    review_task_id=response.review_task_id,
                    polling_interval=self.polling_interval,
                    timeout=self.timeout,
                )

                # Handle the decision
                if final_response.is_approved:
                    # Approved, continue to next tool
                    continue

                elif final_response.is_denied or final_response.is_change_requested:
                    # Denied or changes requested, block execution
                    raise VelatirApprovalDeniedError(
                        f"Tool execution denied for {tool_name}: {final_response.requested_change or 'No reason provided'}",
                        review_task_id=final_response.review_task_id,
                        requested_change=final_response.requested_change,
                    )

            except VelatirTimeoutError as e:
                # Timeout waiting for decision
                raise VelatirTimeoutError(
                    f"Timeout waiting for approval of tool {tool_name} after {self.timeout}s",
                    review_task_id=e.review_task_id,
                    timeout_seconds=self.timeout,
                ) from e

        # All tool calls approved
        return None
