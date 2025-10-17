"""Exception classes for Agent Office SDK."""


class AgentOfficeError(Exception):
    """Base exception for all Agent Office SDK errors."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(AgentOfficeError):
    """Raised when authentication fails (401)."""
    pass


class NotFoundError(AgentOfficeError):
    """Raised when a resource is not found (404)."""
    pass


class ValidationError(AgentOfficeError):
    """Raised when request validation fails (422)."""
    pass


class RateLimitError(AgentOfficeError):
    """Raised when rate limit is exceeded (429)."""
    pass


class ServerError(AgentOfficeError):
    """Raised when server returns a 5xx error."""
    pass

