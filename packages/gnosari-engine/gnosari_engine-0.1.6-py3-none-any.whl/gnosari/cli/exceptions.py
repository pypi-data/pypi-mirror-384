"""CLI exceptions."""


class CLIError(Exception):
    """Base exception for CLI errors."""
    
    def __init__(self, message: str, exit_code: int = 1, suggestion: str = None):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.suggestion = suggestion


class ValidationError(CLIError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(CLIError):
    """Raised when configuration is invalid."""
    pass


class NetworkError(CLIError):
    """Raised when network operations fail."""
    pass


class CommandNotFoundError(CLIError):
    """Raised when a command is not found."""
    pass