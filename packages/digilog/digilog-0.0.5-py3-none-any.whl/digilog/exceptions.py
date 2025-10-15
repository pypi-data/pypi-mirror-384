"""
Custom exceptions for the Digilog client.
"""

class DigilogError(Exception):
    """Base exception for all Digilog-related errors."""
    pass

class AuthenticationError(DigilogError):
    """Raised when authentication fails."""
    pass

class ProjectNotFoundError(DigilogError):
    """Raised when a project is not found."""
    pass

class RunNotFoundError(DigilogError):
    """Raised when a run is not found."""
    pass

class ValidationError(DigilogError):
    """Raised when input validation fails."""
    pass

class APIError(DigilogError):
    """Raised when the API returns an error."""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

class NetworkError(DigilogError):
    """Raised when network communication fails."""
    pass

class ConfigurationError(DigilogError):
    """Raised when there's a configuration issue."""
    pass 