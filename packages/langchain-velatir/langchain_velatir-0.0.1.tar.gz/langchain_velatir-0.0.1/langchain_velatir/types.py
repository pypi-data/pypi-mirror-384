"""Type definitions for LangChain-Velatir integration."""

from enum import Enum
from typing import Literal


class GuardrailMode(str, Enum):
    """Guardrail execution mode."""

    BLOCKING = "blocking"  # Block execution when Velatir denies
    LOGGING = "logging"  # Log Velatir's decisions but continue execution


ReviewTaskState = Literal[
    "Pending",
    "Processing",
    "Approved",
    "RequiresIntervention",
    "Rejected",
    "ChangeRequested",
]
