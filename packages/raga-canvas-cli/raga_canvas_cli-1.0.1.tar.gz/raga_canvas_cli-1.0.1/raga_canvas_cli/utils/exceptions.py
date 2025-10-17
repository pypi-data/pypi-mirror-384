"""Custom exceptions for Raga Canvas CLI."""


class CanvasError(Exception):
    """Base exception for Canvas CLI errors."""
    pass


class AuthenticationError(CanvasError):
    """Authentication related errors."""
    pass


class ConfigurationError(CanvasError):
    """Configuration related errors."""
    pass


class APIError(CanvasError):
    """API related errors."""
    pass


class ValidationError(CanvasError):
    """Validation related errors."""
    pass


class FileSystemError(CanvasError):
    """File system related errors."""
    pass
