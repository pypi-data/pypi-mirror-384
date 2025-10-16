"""Validators for run command arguments following SOLID principles."""

import argparse
import os
from pathlib import Path

from .interfaces import RunCommandValidator


class PathValidator(RunCommandValidator):
    """Validator for path existence and type."""
    
    def __init__(self):
        self._error_message = ""
    
    def validate(self, args: argparse.Namespace) -> bool:
        """Validate that the team path exists."""
        team_path = Path(args.team_path)
        
        if not team_path.exists():
            self._error_message = f"Path not found: {team_path}"
            return False
        
        if not (team_path.is_file() or team_path.is_dir()):
            self._error_message = f"Path must be a file or directory: {team_path}"
            return False
        
        return True
    
    def get_error_message(self) -> str:
        """Get the validation error message."""
        return self._error_message


class ApiKeyValidator(RunCommandValidator):
    """Validator for API key presence."""
    
    def __init__(self):
        self._error_message = ""
    
    def validate(self, args: argparse.Namespace) -> bool:
        """Validate that an API key is available."""
        api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            self._error_message = (
                "OpenAI API key is required. "
                "Set it with --api-key or OPENAI_API_KEY environment variable."
            )
            return False
        
        return True
    
    def get_error_message(self) -> str:
        """Get the validation error message."""
        return self._error_message


class CompositeValidator(RunCommandValidator):
    """Composite validator that runs multiple validators."""
    
    def __init__(self, validators: list[RunCommandValidator]):
        self._validators = validators
        self._error_message = ""
    
    def validate(self, args: argparse.Namespace) -> bool:
        """Run all validators and return True only if all pass."""
        for validator in self._validators:
            if not validator.validate(args):
                self._error_message = validator.get_error_message()
                return False
        
        return True
    
    def get_error_message(self) -> str:
        """Get the validation error message."""
        return self._error_message


class RunCommandValidatorFactory:
    """Factory for creating run command validators."""
    
    def create_validator(self) -> RunCommandValidator:
        """Create a composite validator with all required validations."""
        validators = [
            PathValidator(),
            ApiKeyValidator(),
        ]
        
        return CompositeValidator(validators)