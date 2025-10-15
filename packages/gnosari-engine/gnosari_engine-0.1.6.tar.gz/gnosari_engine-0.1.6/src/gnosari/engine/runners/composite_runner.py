"""
Composite runner that combines all runner functionality
"""

import asyncio
import numpy as np
from typing import Optional, AsyncGenerator, Dict, Any
from ...core.team import Team
from .team_runner import TeamRunner
from .agent_runner import AgentRunner
from .voice_runner import VoiceRunner


class CompositeTeamRunner:
    """Composite runner that delegates to specialized runners."""
    
    def __init__(self, team: Team):
        self.team = team
        self.team_runner = TeamRunner(team)
        self.agent_runner = AgentRunner(team)
        self.voice_runner = VoiceRunner(team)
    
    def set_custom_session_provider(self, provider_factory):
        """Set a custom session provider factory function for all runners."""
        self.team_runner.set_custom_session_provider(provider_factory)
        self.agent_runner.set_custom_session_provider(provider_factory)
        self.voice_runner.set_custom_session_provider(provider_factory)
    
    # Team execution methods
    async def run_team_async(self, message: str, debug: bool = False, 
                            session_id: Optional[str] = None, 
                            session_context: Optional[Dict[str, Any]] = None, 
                            max_turns: Optional[int] = None) -> Dict[str, Any]:
        """Run team asynchronously."""
        return await self.team_runner.run_team_async(message, debug, session_id, session_context, max_turns)
    
    def run_team(self, message: str, debug: bool = False, 
                session_id: Optional[str] = None, 
                max_turns: Optional[int] = None) -> Dict[str, Any]:
        """Run team synchronously."""
        return self.team_runner.run_team(message, debug, session_id, max_turns)
    
    async def run_team_stream(self, message: str, debug: bool = False, 
                             session_id: Optional[str] = None, 
                             session_context: Optional[Dict[str, Any]] = None, 
                             max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run team with streaming outputs."""
        async for response in self.team_runner.run_team_stream(message, debug, session_id, session_context, max_turns):
            yield response
    
    # Agent execution methods
    async def run_agent_until_done_async(self, agent, message: str, 
                                        session_id: Optional[str] = None, 
                                        session_context: Optional[Dict[str, Any]] = None, 
                                        max_turns: Optional[int] = None) -> Dict[str, Any]:
        """Run a specific agent until completion."""
        return await self.agent_runner.run_agent_until_done_async(agent, message, session_id, session_context, max_turns)
    
    async def run_single_agent_stream(self, agent_name: str, message: str, 
                                     debug: bool = False, 
                                     session_id: Optional[str] = None, 
                                     session_context: Optional[Dict[str, Any]] = None, 
                                     max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a specific agent with streaming outputs."""
        async for response in self.agent_runner.run_single_agent_stream(agent_name, message, debug, session_id, session_context, max_turns):
            yield response
    
    # Voice processing methods
    def process_audio_chunk(self, audio_chunk, sample_rate: int = 16000) -> np.ndarray:
        """Process audio chunk from websocket into numpy array."""
        return self.voice_runner.process_audio_chunk(audio_chunk, sample_rate)
    
    async def run_team_voice_stream(self, audio_buffer: np.ndarray, 
                                   debug: bool = False, 
                                   session_id: Optional[str] = None, 
                                   session_context: Optional[Dict[str, Any]] = None, 
                                   max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run team with voice input and streaming audio/text outputs."""
        async for response in self.voice_runner.run_team_voice_stream(audio_buffer, debug, session_id, session_context, max_turns):
            yield response
    
    async def run_single_agent_voice_stream(self, agent_name: str, audio_buffer: np.ndarray, 
                                           debug: bool = False, 
                                           session_id: Optional[str] = None, 
                                           session_context: Optional[Dict[str, Any]] = None, 
                                           max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a specific agent with voice input and streaming audio/text outputs."""
        async for response in self.voice_runner.run_single_agent_voice_stream(agent_name, audio_buffer, debug, session_id, session_context, max_turns):
            yield response