"""Velatir API client wrapper for LangChain integration."""

import time
from typing import Any, Optional

try:
    import velatir
    from velatir import Client as VelatirSDKClient
    from velatir.models import VelatirResponse
except ImportError:
    # For testing when velatir SDK is not installed
    try:
        from tests import mock_velatir as velatir  # type: ignore
        from tests.mock_velatir import Client as VelatirSDKClient, VelatirResponse  # type: ignore
    except ImportError:
        raise ImportError("velatir SDK is required. Install it with: pip install velatir")

from langchain_velatir.exceptions import VelatirTimeoutError


class VelatirClient:
    """
    Wrapper around the Velatir SDK client for LangChain integration.

    Provides simplified methods for creating review tasks and waiting for approvals
    with LangChain-specific error handling and state management.
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ):
        """
        Initialize the Velatir client wrapper.

        Args:
            api_key: Velatir API key
            base_url: Optional custom API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_backoff: Base backoff time in seconds for retries
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        # Initialize the underlying Velatir SDK client
        self._client = VelatirSDKClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )

    async def create_review_task(
        self,
        function_name: str,
        args: dict[str, Any],
        doc: Optional[str] = None,
        llm_explanation: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        parent_review_task_id: Optional[str] = None,
    ) -> VelatirResponse:
        """
        Create a review task in Velatir.

        Args:
            function_name: Name of the function/operation being reviewed
            args: Arguments/data to be reviewed
            doc: Optional documentation/description
            llm_explanation: Optional LLM-generated explanation
            metadata: Optional additional metadata
            parent_review_task_id: Optional parent review task ID

        Returns:
            VelatirResponse with review_task_id and state
        """
        return await self._client.create_review_task(
            function_name=function_name,
            args=args,
            doc=doc,
            llm_explanation=llm_explanation,
            metadata=metadata,
            parent_review_task_id=parent_review_task_id,
        )

    async def get_review_task_status(self, review_task_id: str) -> VelatirResponse:
        """
        Get the current status of a review task.

        Args:
            review_task_id: ID of the review task

        Returns:
            VelatirResponse with current state
        """
        return await self._client.get_review_task_status(review_task_id)

    async def wait_for_approval(
        self,
        review_task_id: str,
        polling_interval: float = 5.0,
        timeout: Optional[float] = None,
    ) -> VelatirResponse:
        """
        Wait for a review task to be approved or denied.

        Args:
            review_task_id: ID of the review task
            polling_interval: Seconds between polling attempts
            timeout: Optional timeout in seconds (None for infinite)

        Returns:
            VelatirResponse with final state

        Raises:
            VelatirTimeoutError: If timeout is reached before completion
        """
        start_time = time.time()
        max_attempts = None

        if timeout is not None:
            # Calculate max attempts based on timeout and polling interval
            max_attempts = int(timeout / polling_interval) + 1

        try:
            response = await self._client.wait_for_approval(
                review_task_id=review_task_id,
                polling_interval=polling_interval,
                max_attempts=max_attempts,
            )
            return response
        except velatir.VelatirTimeoutError as e:
            # Re-raise as our custom timeout error
            elapsed = time.time() - start_time
            raise VelatirTimeoutError(
                f"Approval timeout after {elapsed:.1f}s waiting for review task {review_task_id}",
                review_task_id=review_task_id,
                timeout_seconds=elapsed,
            ) from e

    def create_review_task_sync(
        self,
        function_name: str,
        args: dict[str, Any],
        doc: Optional[str] = None,
        llm_explanation: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        parent_review_task_id: Optional[str] = None,
    ) -> VelatirResponse:
        """Synchronous version of create_review_task."""
        return self._client.create_review_task_sync(
            function_name=function_name,
            args=args,
            doc=doc,
            llm_explanation=llm_explanation,
            metadata=metadata,
            parent_review_task_id=parent_review_task_id,
        )

    def get_review_task_status_sync(self, review_task_id: str) -> VelatirResponse:
        """Synchronous version of get_review_task_status."""
        return self._client.get_review_task_status_sync(review_task_id)

    def wait_for_approval_sync(
        self,
        review_task_id: str,
        polling_interval: float = 5.0,
        timeout: Optional[float] = None,
    ) -> VelatirResponse:
        """Synchronous version of wait_for_approval."""
        start_time = time.time()
        max_attempts = None

        if timeout is not None:
            max_attempts = int(timeout / polling_interval) + 1

        try:
            response = self._client.wait_for_approval_sync(
                review_task_id=review_task_id,
                polling_interval=polling_interval,
                max_attempts=max_attempts,
            )
            return response
        except velatir.VelatirTimeoutError as e:
            elapsed = time.time() - start_time
            raise VelatirTimeoutError(
                f"Approval timeout after {elapsed:.1f}s waiting for review task {review_task_id}",
                review_task_id=review_task_id,
                timeout_seconds=elapsed,
            ) from e

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()

    async def __aenter__(self) -> "VelatirClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
