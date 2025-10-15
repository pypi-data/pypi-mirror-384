"""CLI schemas and data models."""

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class CommandResponse:
    """Response from command execution."""
    
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    exit_code: int = 0


@dataclass
class ValidationResult:
    """Result of input validation."""
    
    is_valid: bool
    error_message: Optional[str] = None
    warnings: Optional[list] = None