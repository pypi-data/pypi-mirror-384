"""
Team Runner - Uses OpenAI Agents SDK Runner to execute teams.

This module now uses a modular architecture with specialized runners.
For backward compatibility, it exposes the same interface as before.
"""

# Import the new modular team runner
from .runners import CompositeTeamRunner

# For backward compatibility, alias the composite runner
TeamRunner = CompositeTeamRunner

__all__ = ["TeamRunner"]