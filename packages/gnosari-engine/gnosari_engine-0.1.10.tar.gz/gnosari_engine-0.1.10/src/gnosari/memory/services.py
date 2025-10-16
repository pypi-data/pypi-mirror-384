"""Learning processor service implementations following SOLID principles."""

import json
import tempfile
import yaml
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from ..schemas.learning import LearningError, LearningContext
from ..sessions.database import DatabaseSession
from ..utils.logging import get_logger
from .interfaces import (
    SessionRetriever, 
    LearningAgentExecutor, 
    MemoryComparer, 
    MemoryUpdater,
    ProgressReporter
)
from .manager import MemoryManager

logger = get_logger(__name__)


class DatabaseSessionRetriever(SessionRetriever):
    """Retrieves sessions from database for learning."""
    
    def __init__(self, database_url: str):
        """Initialize with database URL."""
        self.database_url = database_url
        self._database_session: Optional[DatabaseSession] = None
    
    async def _get_database_session(self) -> DatabaseSession:
        """Get or create database session."""
        if self._database_session is None:
            self._database_session = DatabaseSession(
                session_id="learning_query_session",
                database_url=self.database_url,
                create_tables=True
            )
        return self._database_session
    
    async def retrieve_sessions(self, 
                              team_identifier: str, 
                              agent_name: str, 
                              session_limit: int,
                              team_wide_learning: bool = False) -> List[Dict[str, Any]]:
        """Retrieve sessions from database."""
        try:
            db_session = await self._get_database_session()
            
            # Retrieve sessions based on learning strategy
            if team_wide_learning:
                sessions = await db_session.get_sessions_by_team_or_agent(
                    team_identifier=team_identifier,
                    agent_identifier=None,  # All agents in team
                    limit=session_limit
                )
                logger.info(f"Retrieved {len(sessions)} team-wide sessions for agent {agent_name} learning")
            else:
                sessions = await db_session.get_sessions_by_team_or_agent(
                    team_identifier=team_identifier,
                    agent_identifier=agent_name,
                    limit=session_limit
                )
                logger.info(f"Retrieved {len(sessions)} agent-specific sessions for {agent_name}")
            
            # Filter sessions with meaningful content
            filtered_sessions = []
            for session in sessions:
                if session.get("messages") and len(session["messages"]) > 0:
                    filtered_sessions.append(session)
            
            logger.info(f"Filtered to {len(filtered_sessions)} sessions with messages")
            return filtered_sessions
            
        except Exception as e:
            logger.error(f"Failed to retrieve sessions: {e}")
            raise LearningError(f"Session retrieval failed: {e}", "SESSION_RETRIEVAL_ERROR")


class TeamRunnerLearningAgentExecutor(LearningAgentExecutor):
    """Executes learning agents using TeamRunner infrastructure."""
    
    async def execute_learning_agent(self,
                                   learning_agent_config: Dict[str, Any],
                                   target_agent_name: str,
                                   current_memory: str,
                                   sessions: List[Dict[str, Any]],
                                   learning_context: LearningContext,
                                   progress_callback = None) -> Optional[str]:
        """Execute learning agent using TeamRunner."""
        try:
            from ..prompts.prompts import build_learning_agent_system_prompt
            
            # Build specialized learning prompt
            agent_config, team_directory = await self._extract_agent_context(learning_context)
            
            prompt_sections = build_learning_agent_system_prompt(
                learning_agent_config=learning_agent_config,
                target_agent_name=target_agent_name,
                target_agent_memory=current_memory,
                session_data=sessions,
                learning_context=learning_context.model_dump(),
                agent_config=agent_config,
                team_directory=team_directory
            )
            
            # Create learning team configuration
            learning_instructions = "\n".join(prompt_sections["background"])
            learning_team_config = {
                "name": "Learning Team",
                "agents": [{
                    "name": "LearningAgent",
                    "instructions": learning_instructions,
                    "model": learning_agent_config.get("model", "gpt-4o"),
                    "temperature": learning_agent_config.get("temperature", 0.1),
                    "orchestrator": True,
                    "tools": []
                }]
            }
            
            # Execute learning agent
            return await self._run_learning_team(
                learning_team_config, 
                target_agent_name, 
                progress_callback
            )
            
        except Exception as e:
            logger.error(f"Learning agent execution failed: {e}")
            raise LearningError(f"Learning agent execution failed: {e}", "LEARNING_AGENT_ERROR")
    
    async def _extract_agent_context(self, learning_context: LearningContext):
        """Extract agent configuration for learning specialization."""
        agent_config = None
        team_directory = None
        
        if hasattr(learning_context, 'team_path') and learning_context.team_path:
            team_path = Path(learning_context.team_path)
            team_directory = team_path if team_path.is_dir() else team_path.parent
            
            try:
                from ..engine.config.team_configuration_manager import TeamConfigurationManager
                config_manager = TeamConfigurationManager(team_directory)
                team_data = config_manager.get_merged_config()
                
                # Find agent configuration
                agents_data = team_data.get('agents', [])
                for agent_data in agents_data:
                    agent_name = agent_data.get('name', '').lower()
                    target_name = learning_context.agent_names[0].lower() if learning_context.agent_names else ''
                    
                    if agent_name == target_name or agent_data.get('id', '').lower() == target_name:
                        agent_config = agent_data
                        break
                
                # Check overrides
                overrides = team_data.get('overrides', {}).get('agents', {})
                if target_name in overrides:
                    if agent_config is None:
                        agent_config = {}
                    agent_config.update(overrides[target_name])
                    
            except Exception as e:
                logger.warning(f"Failed to load agent config for specialization: {e}")
        
        return agent_config, team_directory
    
    async def _run_learning_team(self, 
                               learning_team_config: Dict[str, Any], 
                               target_agent_name: str,
                               progress_callback) -> Optional[Dict[str, Any]]:
        """Run the learning team and extract results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(learning_team_config, temp_file, default_flow_style=False)
            temp_config_path = temp_file.name
        
        try:
            from ..engine.builder import TeamBuilder
            from ..engine.runner import TeamRunner
            
            # Build and run learning team
            team_builder = TeamBuilder()
            learning_team = await team_builder.build_team(temp_config_path)
            team_runner = TeamRunner(learning_team)
            
            # Generate unique session ID
            learning_session_id = f"learning-{target_agent_name}-{str(uuid.uuid4())[:8]}"
            
            # Report learning start
            if progress_callback:
                progress_callback.report_learning_start(target_agent_name, learning_session_id)
            
            # Execute learning team
            session_context = {
                'team_identifier': temp_config_path,
                'session_id': learning_session_id
            }
            
            team_result = await team_runner.run_team_async(
                message="Please analyze the agent memory and conversation history, then provide your response according to the format requirements.",
                session_id=learning_session_id,
                session_context=session_context
            )
            
            # Extract and parse learning agent response
            return await self._extract_learning_response(team_result, target_agent_name, progress_callback)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_config_path)
            except OSError:
                pass
    
    async def _extract_learning_response(self, 
                                       team_result: Dict[str, Any], 
                                       target_agent_name: str,
                                       progress_callback) -> Optional[str]:
        """Extract and parse learning agent response."""
        learning_agent_response = ""
        
        # Extract response from team result
        if team_result and 'outputs' in team_result:
            outputs = team_result['outputs']
            for output in outputs:
                if output.get('type') == 'completion' and output.get('content'):
                    learning_agent_response = output['content']
                    break
        
        logger.info(f"DEBUG: Learning agent raw response: {repr(learning_agent_response[:200])}")
        
        # Parse response as string memory
        updated_memory = await self._parse_memory_response(learning_agent_response)
        has_changes = updated_memory is not None and updated_memory != ""
        
        # Report completion
        if progress_callback:
            progress_callback.report_learning_complete(target_agent_name, has_changes)
        
        return updated_memory if has_changes else None
    
    async def _parse_memory_response(self, response: str) -> Optional[str]:
        """Parse learning agent response as simple string memory."""
        if not response or response.strip() in ['', '""', "''", '{}', 'null', 'None']:
            logger.debug("Learning agent returned empty or null response")
            return None
        
        # Return the raw response as string memory
        memory_content = response.strip()
        logger.info(f"Learning agent provided memory update (length: {len(memory_content)})")
        logger.debug(f"Memory content preview: {repr(memory_content[:200])}")
        
        return memory_content


class SimpleMemoryComparer(MemoryComparer):
    """Simple string-based memory comparison."""
    
    def has_changes(self, 
                   current_memory: str, 
                   new_memory: Optional[str]) -> bool:
        """Simple comparison of current memory vs new memory string."""
        if not new_memory or new_memory.strip() == "":
            logger.debug("New memory is empty or None")
            return False
        
        # Get current memory as string
        current_normalized = current_memory.strip() if current_memory else ""
        new_normalized = new_memory.strip()
        
        has_changes = current_normalized != new_normalized
        
        logger.info(f"Memory comparison result: has_changes={has_changes}")
        logger.debug(f"Current memory length: {len(current_normalized)}")
        logger.debug(f"New memory length: {len(new_normalized)}")
        logger.debug(f"Current memory preview: {repr(current_normalized[:100])}")
        logger.debug(f"New memory preview: {repr(new_normalized[:100])}")
        
        return has_changes


class ProviderMemoryUpdater(MemoryUpdater):
    """Updates memory using configured memory provider."""
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize with memory manager."""
        self.memory_manager = memory_manager
    
    async def update_memory(self,
                          team_path: str,
                          agent_name: str,
                          new_memory: str) -> Optional[str]:
        """Update memory using memory manager."""
        try:
            backup_path = await self.memory_manager.update_agent_memory(
                team_path=team_path,
                agent_name=agent_name,
                new_memory=new_memory
            )
            
            logger.info(f"Successfully updated memory for agent {agent_name}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            raise LearningError(f"Memory update failed: {e}", "MEMORY_UPDATE_ERROR")


class CallbackProgressReporter(ProgressReporter):
    """Reports progress using callback functions."""
    
    def __init__(self, callback):
        """Initialize with callback object."""
        self.callback = callback
    
    def report_session_retrieval_start(self, agent_name: str, team_identifier: str) -> None:
        """Report session retrieval start."""
        if self.callback and hasattr(self.callback, 'on_session_retrieval_start'):
            self.callback.on_session_retrieval_start(agent_name, team_identifier)
    
    def report_sessions_retrieved(self, agent_name: str, session_count: int, time_period: str) -> None:
        """Report sessions retrieved."""
        if self.callback and hasattr(self.callback, 'on_sessions_retrieved'):
            self.callback.on_sessions_retrieved(agent_name, session_count, time_period)
    
    def report_learning_start(self, agent_name: str, session_id: str) -> None:
        """Report learning start."""
        if self.callback and hasattr(self.callback, 'on_learning_agent_start'):
            self.callback.on_learning_agent_start(agent_name, session_id)
    
    def report_learning_complete(self, agent_name: str, has_changes: bool) -> None:
        """Report learning complete."""
        if self.callback and hasattr(self.callback, 'on_learning_agent_complete'):
            self.callback.on_learning_agent_complete(agent_name, has_changes)
    
    def report_memory_updated(self, agent_name: str, backup_path: str) -> None:
        """Report memory updated."""
        if self.callback and hasattr(self.callback, 'on_instructions_updated'):
            self.callback.on_instructions_updated(agent_name, backup_path)