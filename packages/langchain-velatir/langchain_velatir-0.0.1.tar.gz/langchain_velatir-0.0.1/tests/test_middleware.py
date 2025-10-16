"""Unit tests for Velatir middleware components."""

import pytest

from langchain_velatir.middleware import VelatirGuardrailMiddleware, VelatirHITLMiddleware
from langchain_velatir.types import GuardrailMode


class TestVelatirGuardrailMiddleware:
    """Tests for VelatirGuardrailMiddleware."""

    def test_init_minimal(self):
        """Test middleware initialization with minimal parameters."""
        middleware = VelatirGuardrailMiddleware(api_key="test-key")

        assert middleware.velatir_client is not None
        assert middleware.mode == GuardrailMode.BLOCKING
        assert middleware.approval_timeout == 30.0
        assert middleware.polling_interval == 2.0

    def test_init_blocking_mode(self):
        """Test middleware initialization in blocking mode."""
        middleware = VelatirGuardrailMiddleware(api_key="test-key", mode="blocking")

        assert middleware.mode == GuardrailMode.BLOCKING

    def test_init_logging_mode(self):
        """Test middleware initialization in logging mode."""
        middleware = VelatirGuardrailMiddleware(api_key="test-key", mode="logging")

        assert middleware.mode == GuardrailMode.LOGGING

    def test_init_custom_timeouts(self):
        """Test middleware initialization with custom timeout values."""
        middleware = VelatirGuardrailMiddleware(
            api_key="test-key",
            timeout=20.0,
            approval_timeout=60.0,
            polling_interval=5.0,
        )

        assert middleware.approval_timeout == 60.0
        assert middleware.polling_interval == 5.0

    @pytest.mark.asyncio
    async def test_after_agent_hook_exists(self):
        """Test that after_agent hook exists and is callable."""
        middleware = VelatirGuardrailMiddleware(api_key="test-key")

        assert hasattr(middleware, "after_agent")
        assert callable(middleware.after_agent)


class TestVelatirHITLMiddleware:
    """Tests for VelatirHITLMiddleware."""

    def test_init_default_params(self):
        """Test middleware initialization with default parameters."""
        middleware = VelatirHITLMiddleware(api_key="test-key")

        assert middleware.polling_interval == 5.0
        assert middleware.timeout == 600.0
        assert middleware.require_approval_for is None

    def test_init_custom_params(self):
        """Test middleware initialization with custom parameters."""
        middleware = VelatirHITLMiddleware(
            api_key="test-key",
            polling_interval=2.0,
            timeout=300.0,
            require_approval_for=["delete_file", "send_email"],
        )

        assert middleware.polling_interval == 2.0
        assert middleware.timeout == 300.0
        assert middleware.require_approval_for == ["delete_file", "send_email"]

    @pytest.mark.asyncio
    async def test_modify_model_request_hook_exists(self):
        """Test that modify_model_request hook exists and is callable."""
        middleware = VelatirHITLMiddleware(api_key="test-key")

        assert hasattr(middleware, "modify_model_request")
        assert callable(middleware.modify_model_request)


class TestMiddlewareIntegration:
    """Integration tests for middleware components."""

    @pytest.mark.asyncio
    async def test_both_middleware_can_coexist(self):
        """Test that both middleware types can be instantiated together."""
        guardrails = VelatirGuardrailMiddleware(api_key="test-key")
        hitl = VelatirHITLMiddleware(api_key="test-key")

        assert guardrails is not None
        assert hitl is not None
        assert hasattr(guardrails, "after_agent")
        assert hasattr(hitl, "modify_model_request")
