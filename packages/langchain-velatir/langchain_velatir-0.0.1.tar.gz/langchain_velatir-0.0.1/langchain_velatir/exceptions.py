"""Custom exceptions for LangChain-Velatir integration."""

from typing import Optional


class VelatirMiddlewareError(Exception):
    """Base exception for Velatir middleware errors."""

    pass


class VelatirPolicyViolationError(VelatirMiddlewareError):
    """Raised when a policy violation is detected by Velatir guardrails."""

    def __init__(
        self,
        message: str,
        review_task_id: Optional[str] = None,
        violated_policies: Optional[list[str]] = None,
        requested_change: Optional[str] = None,
    ):
        super().__init__(message)
        self.review_task_id = review_task_id
        self.violated_policies = violated_policies or []
        self.requested_change = requested_change


class VelatirApprovalDeniedError(VelatirMiddlewareError):
    """Raised when a human approval request is denied."""

    def __init__(
        self,
        message: str,
        review_task_id: Optional[str] = None,
        requested_change: Optional[str] = None,
    ):
        super().__init__(message)
        self.review_task_id = review_task_id
        self.requested_change = requested_change


class VelatirTimeoutError(VelatirMiddlewareError):
    """Raised when waiting for approval times out."""

    def __init__(
        self,
        message: str,
        review_task_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        super().__init__(message)
        self.review_task_id = review_task_id
        self.timeout_seconds = timeout_seconds
