"""
LangChain integration for Velatir.

Provides middleware for AI governance, compliance, and human-in-the-loop workflows.
"""

__version__ = "0.0.2"

from langchain_velatir.middleware import (
    VelatirGuardrailMiddleware,
    VelatirHITLMiddleware,
)
from langchain_velatir.exceptions import (
    VelatirMiddlewareError,
    VelatirPolicyViolationError,
    VelatirApprovalDeniedError,
    VelatirTimeoutError,
)

__all__ = [
    "VelatirGuardrailMiddleware",
    "VelatirHITLMiddleware",
    "VelatirMiddlewareError",
    "VelatirPolicyViolationError",
    "VelatirApprovalDeniedError",
    "VelatirTimeoutError",
]
