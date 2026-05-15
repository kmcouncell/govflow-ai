"""Application-specific errors for consistent handling and logging."""


class GovFlowError(Exception):
    """Base error for GovFlow backend."""


class ConfigurationError(GovFlowError):
    """Raised when environment or YAML configuration is invalid or missing."""


class ExternalServiceError(GovFlowError):
    """Raised when an optional external dependency fails; callers may degrade gracefully."""
