from __future__ import annotations

from typing import Any


class ProviderError(Exception):
    """A provider failure that can safely cross the API boundary.

    The agent must not turn one of these errors into a successful chat response:
    doing so obscures configuration and availability failures and can make a
    model failure look like a completed dashboard operation.
    """

    def __init__(
        self,
        provider: str,
        error_type: str,
        message: str,
        *,
        status_code: int | None = None,
        provider_code: str | None = None,
        provider_message: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.error_type = error_type
        self.status_code = status_code
        self.provider_code = provider_code
        self.provider_message = provider_message
        self.retry_after = retry_after


class GeminiRateLimitError(ProviderError):
    """Raised when Gemini rejects a request because the project is rate limited."""

    def __init__(self, message: str = "NEXUS is busy right now. Please wait a few seconds and try again.", retry_after: float | None = None, **kwargs: Any):
        super().__init__("gemini", "RATE_LIMITED", message, retry_after=retry_after, **kwargs)


class GeminiAuthenticationError(ProviderError):
    """Raised for Gemini authentication/configuration failures."""

    def __init__(self, message: str = "Gemini authentication failed.", **kwargs: Any):
        super().__init__("gemini", "AUTHENTICATION_ERROR", message, **kwargs)


class GeminiModelUnavailableError(ProviderError):
    """Raised when the configured Gemini model is unavailable."""

    def __init__(self, message: str = "The configured Gemini model is unavailable.", **kwargs: Any):
        super().__init__("gemini", "MODEL_UNAVAILABLE", message, **kwargs)


class GeminiInvalidRequestError(ProviderError):
    def __init__(self, message: str = "Gemini rejected the request as invalid.", **kwargs: Any):
        super().__init__("gemini", "INVALID_REQUEST", message, **kwargs)


class GeminiNetworkError(ProviderError):
    def __init__(self, message: str = "NEXUS could not reach Gemini.", **kwargs: Any):
        super().__init__("gemini", "NETWORK_ERROR", message, **kwargs)


class GeminiProviderResponseError(ProviderError):
    def __init__(self, message: str = "Gemini returned an unusable response.", **kwargs: Any):
        super().__init__("gemini", "PROVIDER_ERROR", message, **kwargs)


class OllamaProviderError(ProviderError):
    def __init__(self, error_type: str, message: str, **kwargs: Any):
        super().__init__("ollama", error_type, message, **kwargs)
