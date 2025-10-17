"""Agent Office Python SDK - AI-powered document editing for agentic workflows."""

from .client import AgentOffice
from .exceptions import (
    AgentOfficeError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

__version__ = "0.0.2"
__all__ = [
    "AgentOffice",
    "AgentOfficeError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]

