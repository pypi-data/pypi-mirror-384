"""Mock velatir module for testing when the real SDK is not available."""

from typing import Any, Optional
from enum import Enum


class ReviewTaskState(str, Enum):
    """Mock review task states."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REQUIRES_INTERVENTION = "requires_intervention"
    CHANGE_REQUESTED = "change_requested"


class VelatirResponse:
    """Mock Velatir API response."""

    def __init__(
        self,
        review_task_id: str,
        state: ReviewTaskState,
        requested_change: Optional[str] = None,
    ):
        self.review_task_id = review_task_id
        self.state = state
        self.requested_change = requested_change

    @property
    def is_approved(self) -> bool:
        return self.state == ReviewTaskState.APPROVED

    @property
    def is_denied(self) -> bool:
        return self.state == ReviewTaskState.DENIED

    @property
    def is_pending(self) -> bool:
        return self.state == ReviewTaskState.PENDING

    @property
    def is_change_requested(self) -> bool:
        return self.state == ReviewTaskState.CHANGE_REQUESTED

    @property
    def requires_intervention(self) -> bool:
        return self.state == ReviewTaskState.REQUIRES_INTERVENTION


class VelatirTimeoutError(Exception):
    """Mock timeout error."""

    pass


class Client:
    """Mock Velatir SDK client."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    async def create_review_task(
        self,
        function_name: str,
        args: dict[str, Any],
        doc: Optional[str] = None,
        llm_explanation: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        parent_review_task_id: Optional[str] = None,
    ) -> VelatirResponse:
        """Mock create review task."""
        return VelatirResponse(
            review_task_id="mock-task-id",
            state=ReviewTaskState.APPROVED,
        )

    async def get_review_task_status(self, review_task_id: str) -> VelatirResponse:
        """Mock get review task status."""
        return VelatirResponse(
            review_task_id=review_task_id,
            state=ReviewTaskState.APPROVED,
        )

    async def wait_for_approval(
        self,
        review_task_id: str,
        polling_interval: float = 5.0,
        max_attempts: Optional[int] = None,
    ) -> VelatirResponse:
        """Mock wait for approval."""
        return VelatirResponse(
            review_task_id=review_task_id,
            state=ReviewTaskState.APPROVED,
        )

    def create_review_task_sync(
        self,
        function_name: str,
        args: dict[str, Any],
        doc: Optional[str] = None,
        llm_explanation: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        parent_review_task_id: Optional[str] = None,
    ) -> VelatirResponse:
        """Mock create review task sync."""
        return VelatirResponse(
            review_task_id="mock-task-id",
            state=ReviewTaskState.APPROVED,
        )

    def get_review_task_status_sync(self, review_task_id: str) -> VelatirResponse:
        """Mock get review task status sync."""
        return VelatirResponse(
            review_task_id=review_task_id,
            state=ReviewTaskState.APPROVED,
        )

    def wait_for_approval_sync(
        self,
        review_task_id: str,
        polling_interval: float = 5.0,
        max_attempts: Optional[int] = None,
    ) -> VelatirResponse:
        """Mock wait for approval sync."""
        return VelatirResponse(
            review_task_id=review_task_id,
            state=ReviewTaskState.APPROVED,
        )

    async def close(self) -> None:
        """Mock close."""
        pass
