"""Interfaces for the run command system following SOLID principles."""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from ...schemas import CommandResponse
from ....engine.builder import TeamBuilder
from ....engine.runner import TeamRunner


class ConfigurationDetector(ABC):
    """Interface for detecting configuration types."""
    
    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Check if this detector can handle the given path."""
        pass
    
    @abstractmethod
    def get_config_type(self) -> str:
        """Get the configuration type name."""
        pass


class ConfigurationLoader(ABC):
    """Interface for loading different configuration types."""
    
    @abstractmethod
    async def load_configuration(self, path: Path) -> Dict[str, Any]:
        """Load configuration from the given path."""
        pass
    
    @abstractmethod
    def get_team_identifier(self, path: Path) -> str:
        """Extract team identifier from path."""
        pass


class TeamExecutor(ABC):
    """Interface for executing teams with different strategies."""
    
    @abstractmethod
    async def execute_team(
        self,
        runner: TeamRunner,
        message: str,
        agent_name: Optional[str] = None,
        stream: bool = False,
        debug: bool = False,
        session_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
        console: Any = None
    ) -> None:
        """Execute the team with the specified parameters."""
        pass


class RunCommandValidator(ABC):
    """Interface for validating run command arguments."""
    
    @abstractmethod
    def validate(self, args: argparse.Namespace) -> bool:
        """Validate the command arguments."""
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """Get the validation error message."""
        pass