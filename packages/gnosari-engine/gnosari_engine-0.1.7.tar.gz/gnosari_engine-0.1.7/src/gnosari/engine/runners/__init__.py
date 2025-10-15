"""
Modular runners for Gnosari Engine
"""

from .base_runner import BaseRunner
from .team_runner import TeamRunner
from .agent_runner import AgentRunner  
from .voice_runner import VoiceRunner
from .session_manager import SessionManager
from .cleanup_manager import CleanupManager
from .composite_runner import CompositeTeamRunner

# For backward compatibility, expose CompositeTeamRunner as TeamRunner
TeamRunner = CompositeTeamRunner

__all__ = [
    "BaseRunner",
    "TeamRunner",  # This is now CompositeTeamRunner
    "AgentRunner",
    "VoiceRunner", 
    "SessionManager",
    "CleanupManager",
    "CompositeTeamRunner"
]