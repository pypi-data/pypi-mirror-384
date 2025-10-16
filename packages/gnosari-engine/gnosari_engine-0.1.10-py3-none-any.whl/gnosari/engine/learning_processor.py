"""Learning processor for agent improvement based on session history."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Protocol
from datetime import datetime
from pathlib import Path

from ..schemas.learning import (
    LearningConfig, 
    LearningRequest, 
    LearningResponse, 
    LearningContext,
    SessionContext as LearningSessionContext,
    LearningTaskStatus,
    LearningError
)
from ..schemas.event import create_event
from ..sessions.database import DatabaseSession
from .queue_manager import QueueManager
from ..memory.factory import get_default_memory_manager
from ..memory.manager import MemoryManager
# Import TeamBuilder locally to avoid circular imports
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LearningProgressCallback(Protocol):
    """Protocol for learning progress callbacks."""
    
    def on_session_retrieval_start(self, agent_name: str, team_identifier: str) -> None:
        """Called when session retrieval starts for an agent."""
        ...
    
    def on_sessions_retrieved(self, agent_name: str, session_count: int, time_period: str) -> None:
        """Called when sessions are successfully retrieved."""
        ...
    
    def on_learning_agent_start(self, agent_name: str, learning_session_id: str) -> None:
        """Called when learning agent execution starts."""
        ...
    
    def on_learning_agent_complete(self, agent_name: str, has_changes: bool) -> None:
        """Called when learning agent execution completes."""
        ...
    
    def on_instructions_updated(self, agent_name: str, backup_path: str) -> None:
        """Called when agent instructions are successfully updated."""
        ...


class LearningProcessor:
    """Processes learning for agents based on session history."""
    
    def __init__(self, 
                 database_url: Optional[str] = None,
                 queue_manager: Optional[QueueManager] = None,
                 memory_manager: Optional[MemoryManager] = None):
        """Initialize learning processor.
        
        Args:
            database_url: Database URL for session retrieval
            queue_manager: Optional queue manager for async processing
            memory_manager: Optional memory manager for agent memory operations
        """
        self.database_url = database_url or "sqlite+aiosqlite:///conversations.db"
        self.queue_manager = queue_manager
        self._memory_manager = memory_manager
        self._team_builder = None
        self._task_cache: Dict[str, LearningTaskStatus] = {}
        self._database_session: Optional[DatabaseSession] = None
    
    async def _get_database_session(self) -> DatabaseSession:
        """Get or create database session instance."""
        if self._database_session is None:
            self._database_session = DatabaseSession(
                session_id="learning_query_session",
                database_url=self.database_url,
                create_tables=True
            )
        return self._database_session
    
    def _get_memory_manager(self) -> MemoryManager:
        """Get or create memory manager instance."""
        if self._memory_manager is None:
            self._memory_manager = get_default_memory_manager()
        return self._memory_manager
        
    async def process_learning_sync(self, request: LearningRequest, progress_callback: Optional[LearningProgressCallback] = None) -> List[LearningResponse]:
        """Execute learning synchronously and return results immediately.
        
        Args:
            request: Learning request configuration
            
        Returns:
            List of learning responses for each agent
            
        Raises:
            LearningError: If learning processing fails
        """
        try:
            logger.info(f"Starting synchronous learning for team: {request.team_path}")
            
            # Load team configuration
            team_config = await self._load_team_config(request.team_path)
            learning_config = self._extract_learning_config(team_config)
            
            if not learning_config.enabled:
                raise LearningError("Learning is disabled for this team", "LEARNING_DISABLED")
            
            # Get target agents
            target_agent_ids = self._get_target_agents(team_config, request.target_agents)
            # Process each agent
            results = []
            for agent_id in target_agent_ids:
                try:
                    result = await self._process_single_agent_learning(
                        agent_id=agent_id,
                        team_config=team_config,
                        learning_config=learning_config,
                        request=request,
                        progress_callback=progress_callback
                    )

                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to process learning for agent {agent_id}: {e}")
                    # Create error response
                    error_result = LearningResponse(
                        agent_name=agent_id,
                        original_memory=None,
                        updated_memory=None,
                        has_changes=False,
                        learning_summary=f"Learning failed: {str(e)}",
                        confidence_score=0.0
                    )
                    results.append(error_result)
            
            logger.info(f"Completed synchronous learning for {len(results)} agents")
            return results
            
        except Exception as e:
            logger.error(f"Synchronous learning failed: {e}")
            raise LearningError(f"Learning processing failed: {e}", "PROCESSING_ERROR")
    
    async def process_learning_async(self, request: LearningRequest) -> List[str]:
        """Queue learning for async processing and return task IDs.
        
        Args:
            request: Learning request configuration
            
        Returns:
            List of task IDs for monitoring
            
        Raises:
            LearningError: If task queuing fails
        """
        if not self.queue_manager:
            raise LearningError("Queue manager not configured for async processing", "NO_QUEUE_MANAGER")
        
        try:
            logger.info(f"Starting asynchronous learning for team: {request.team_path}")
            
            # Load team configuration
            team_config = await self._load_team_config(request.team_path)
            learning_config = self._extract_learning_config(team_config)
            
            if not learning_config.enabled:
                raise LearningError("Learning is disabled for this team", "LEARNING_DISABLED")
            
            # Get target agents
            target_agent_ids = self._get_target_agents(team_config, request.target_agents)
            
            # Queue learning tasks for each agent
            task_ids = []
            queue_name = learning_config.queue_name or "learning_queue"
            
            for agent_id in target_agent_ids:
                try:
                    # Create learning event
                    learning_event = create_event(
                        event_type="agent_learning",
                        source="learning_processor",
                        data={
                            "agent_id": agent_id,
                            "team_path": request.team_path,
                            "team_config": team_config,
                            "learning_config": learning_config.model_dump(),
                            "session_context": request.session_context
                        },
                        metadata={
                            "learning_mode": "async",
                            "agent_id": agent_id,
                            "team_identifier": team_config.get("id", "unknown")
                        }
                    )
                    
                    # Publish to queue
                    task_id = await self.queue_manager.publish_to_queue(queue_name, learning_event)
                    task_ids.append(task_id)
                    
                    # Store task status
                    self._task_cache[task_id] = LearningTaskStatus(
                        task_id=task_id,
                        status="pending",
                        agent_name=agent_id,
                        team_path=request.team_path,
                        created_at=datetime.utcnow().isoformat(),
                        updated_at=datetime.utcnow().isoformat()
                    )
                    
                    logger.debug(f"Queued learning task {task_id} for agent {agent_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to queue learning task for agent {agent_id}: {e}")
                    # Continue with other agents
            
            if not task_ids:
                raise LearningError("No learning tasks could be queued", "NO_TASKS_QUEUED")
            
            logger.info(f"Queued {len(task_ids)} learning tasks for asynchronous processing")
            return task_ids
            
        except LearningError:
            raise
        except Exception as e:
            logger.error(f"Asynchronous learning failed: {e}")
            raise LearningError(f"Task queuing failed: {e}", "QUEUING_ERROR")
    
    async def get_learning_status(self, task_id: str) -> Optional[LearningTaskStatus]:
        """Get status of async learning task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status or None if not found
        """
        return self._task_cache.get(task_id)
    
    async def wait_for_learning_completion(self, 
                                         task_ids: List[str], 
                                         timeout: int = 300) -> List[LearningResponse]:
        """Wait for async learning tasks to complete.
        
        Args:
            task_ids: List of task IDs to wait for
            timeout: Maximum wait time in seconds
            
        Returns:
            List of learning responses
            
        Raises:
            LearningError: If tasks don't complete within timeout
        """
        start_time = datetime.utcnow()
        completed_results = []
        
        while len(completed_results) < len(task_ids):
            # Check if timeout exceeded
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise LearningError(
                    f"Learning tasks timed out after {timeout} seconds", 
                    "TIMEOUT_ERROR"
                )
            
            # Check status of pending tasks
            for task_id in task_ids:
                if any(r.agent_name == self._task_cache.get(task_id, {}).agent_name 
                      for r in completed_results):
                    continue  # Already completed
                
                task_status = await self.get_learning_status(task_id)
                if task_status and task_status.status == "completed" and task_status.result:
                    completed_results.append(task_status.result)
                elif task_status and task_status.status == "failed":
                    # Add error result
                    error_result = LearningResponse(
                        agent_name=task_status.agent_name,
                        original_memory=None,
                        updated_memory=None,
                        has_changes=False,
                        learning_summary=f"Task failed: {task_status.error_message}",
                        confidence_score=0.0
                    )
                    completed_results.append(error_result)
            
            # Wait before checking again
            await asyncio.sleep(1)
        
        return completed_results
    
    async def _process_single_agent_learning(self,
                                           agent_id: str,
                                           team_config: Dict[str, Any],
                                           learning_config: LearningConfig,
                                           request: LearningRequest,
                                           progress_callback: Optional[LearningProgressCallback] = None) -> LearningResponse:
        """Process learning for a single agent using new memory-focused architecture.
        
        Args:
            agent_id: ID of the agent to improve
            team_config: Full team configuration
            learning_config: Learning configuration
            request: Original learning request
            
        Returns:
            Learning response with results
        """
        try:
            logger.info(f"Processing learning for agent using new memory architecture: {agent_id}")
            
            # Import and use new memory learning processor
            from ..memory.learning_processor import MemoryLearningProcessorFactory
            
            # Create memory learning processor with proper dependencies
            memory_processor = MemoryLearningProcessorFactory.create_processor(
                database_url=self.database_url,
                progress_callback=progress_callback
            )
            
            # Use new memory-focused learning processor
            result = await memory_processor.process_agent_learning(
                team_path=request.team_path,
                agent_name=agent_id,
                team_config=team_config,
                learning_config=learning_config,
                team_wide_learning=request.team_wide_learning
            )
            
            logger.info(f"Completed learning for agent {agent_id} using new architecture")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process learning for agent {agent_id}: {e}")
            raise LearningError(f"Agent learning failed: {e}", "AGENT_LEARNING_ERROR", agent_id)
    
    async def _load_team_config(self, team_path: str) -> Dict[str, Any]:
        """Load team configuration from file or directory."""
        try:
            from pathlib import Path
            from .config.configuration_manager import ConfigurationManager
            
            team_path_obj = Path(team_path)
            
            if team_path_obj.is_file():
                # Monolithic YAML file
                from .config.config_loader import ConfigLoader
                loader = ConfigLoader()
                return loader.load_team_config(team_path)
            elif team_path_obj.is_dir():
                # Modular directory configuration
                config_manager = ConfigurationManager()
                modular_config = await config_manager.load_team_from_directory(team_path_obj)
                # Convert to legacy format for compatibility
                return await config_manager.convert_to_legacy_format(modular_config)
            else:
                raise LearningError(f"Team path does not exist: {team_path}", "INVALID_TEAM_PATH")
                
        except LearningError:
            raise
        except Exception as e:
            raise LearningError(f"Failed to load team configuration: {e}", "CONFIG_LOAD_ERROR")
    
    def _extract_learning_config(self, team_config: Dict[str, Any]) -> LearningConfig:
        """Extract learning configuration from team config."""
        learning_data = team_config.get("learning", {})
        logger.debug(f"Extracting learning config from team config: {learning_data}")
        logger.debug(f"Full team config keys: {list(team_config.keys())}")
        
        if not learning_data:
            # Return default disabled configuration
            logger.warning("No learning configuration found in team config")
            return LearningConfig(enabled=False, learning_agent="")
        
        try:
            return LearningConfig(**learning_data)
        except Exception as e:
            logger.error(f"Invalid learning configuration: {e}, data: {learning_data}")
            raise LearningError(f"Invalid learning configuration: {e}", "INVALID_LEARNING_CONFIG")
    
    def _get_target_agents(self, team_config: Dict[str, Any], target_agents: Optional[List[str]]) -> List[str]:
        """Get list of agent IDs to process learning for."""
        # Get all agent IDs (use id field if available, otherwise use filename)
        all_agent_ids = []
        for agent in team_config.get("agents", []):
            agent_id = agent.get("id") or agent.get("name", "").lower().replace(" ", "_")
            all_agent_ids.append(agent_id)
        
        if target_agents:
            # Validate that specified agents exist
            missing_agents = set(target_agents) - set(all_agent_ids)
            if missing_agents:
                raise LearningError(
                    f"Agents not found: {', '.join(missing_agents)}", 
                    "AGENTS_NOT_FOUND"
                )
            return target_agents
        
        # Filter out learning agents (they don't learn from themselves)
        learning_config = self._extract_learning_config(team_config)
        learning_agent_id = learning_config.learning_agent
        
        return [agent_id for agent_id in all_agent_ids if agent_id != learning_agent_id]
    
    def _get_agent_config(self, team_config: Dict[str, Any], agent_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent by ID."""
        for agent in team_config.get("agents", []):
            # Check both id field and generated ID from name
            current_id = agent.get("id") or agent.get("name", "").lower().replace(" ", "_")
            if current_id == agent_id:
                return agent
        return None
    
    def _calculate_time_period(self, sessions: List[Dict[str, Any]]) -> str:
        """Calculate time period covered by sessions."""
        if not sessions:
            return "No sessions"
        
        try:
            timestamps = []
            for session in sessions:
                if "created_at" in session:
                    timestamps.append(datetime.fromisoformat(session["created_at"].replace('Z', '+00:00')))
            
            if not timestamps:
                return "Unknown period"
            
            start_time = min(timestamps)
            end_time = max(timestamps)
            duration = end_time - start_time
            
            return f"{start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} ({duration.days} days)"
            
        except Exception:
            return "Unknown period"
    
    async def _execute_learning_agent(self,
                                    learning_agent_config: Dict[str, Any],
                                    target_agent_name: str,
                                    target_agent_memory: Dict[str, Any],
                                    session_data: List[Dict[str, Any]],
                                    learning_context: LearningContext,
                                    progress_callback: Optional[LearningProgressCallback] = None) -> Optional[Dict[str, Any]]:
        """Execute learning agent using proper team runner infrastructure."""
        try:
            # Import here to avoid circular imports
            from ..prompts.prompts import build_learning_agent_system_prompt
            
            # Build system prompt with specialized learning strategies
            # Extract agent configuration for learning specialization
            agent_config = None
            team_directory = None
            
            # Try to get agent config from team_config for learning specialization
            if hasattr(learning_context, 'team_path') and learning_context.team_path:
                team_path = Path(learning_context.team_path)
                team_directory = team_path if team_path.is_dir() else team_path.parent
                
                # Find agent config from team configuration
                try:
                    from .config.team_configuration_manager import TeamConfigurationManager
                    config_manager = TeamConfigurationManager(team_directory)
                    team_data = config_manager.get_merged_config()
                    
                    # Look for agent config in the team data
                    agents_data = team_data.get('agents', [])
                    for agent_data in agents_data:
                        agent_name = agent_data.get('name', '').lower()
                        if agent_name == target_agent_name.lower() or agent_data.get('id', '').lower() == target_agent_name.lower():
                            agent_config = agent_data
                            break
                    
                    # Also check overrides for learning configuration
                    overrides = team_data.get('overrides', {}).get('agents', {})
                    if target_agent_name.lower() in overrides:
                        if agent_config is None:
                            agent_config = {}
                        agent_config.update(overrides[target_agent_name.lower()])
                        
                except Exception as e:
                    logger.warning(f"Failed to load agent config for learning specialization: {e}")
                    agent_config = None
            
            # Build system prompt with specialization support (now using memory)
            prompt_sections = build_learning_agent_system_prompt(
                learning_agent_config=learning_agent_config,
                target_agent_name=target_agent_name,
                target_agent_memory=target_agent_memory,
                session_data=session_data,
                learning_context=learning_context.model_dump(),
                agent_config=agent_config,
                team_directory=team_directory
            )

            
            # Combine prompt sections - this becomes the learning agent's instructions
            learning_instructions = "\n".join(prompt_sections["background"])
            
            # Create a minimal team config just for the learning agent
            learning_team_config = {
                "name": "Learning Team",
                "agents": [{
                    "name": "LearningAgent",
                    "instructions": learning_instructions,
                    "model": learning_agent_config.get("model", "gpt-4o"),
                    "temperature": learning_agent_config.get("temperature", 0.1),
                    "orchestrator": True,
                    "tools": []  # Learning agent doesn't need tools
                }]
            }
            
            # Build and run the learning agent team
            from .builder import TeamBuilder
            from .runner import TeamRunner
            import tempfile
            import yaml
            import os
            
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                yaml.dump(learning_team_config, temp_file, default_flow_style=False)
                temp_config_path = temp_file.name
            
            try:
                # Use exact same execution path as CLI team run command
                from gnosari.cli.commands.run.team_service import create_team_execution_service
                import uuid
                
                team_service = create_team_execution_service()
                
                # Create unique session for learning
                learning_session_id = f"learning-{target_agent_name}-{str(uuid.uuid4())[:8]}"
                
                # Notify learning agent execution start
                if progress_callback:
                    progress_callback.on_learning_agent_start(target_agent_name, learning_session_id)
                
                # Get console from progress callback if available
                console = None
                if progress_callback and hasattr(progress_callback, 'console'):
                    console = progress_callback.console
                
                # Build and run learning team with streaming - reuse team run streaming logic
                from .builder import TeamBuilder
                from .runner import TeamRunner
                
                team_builder = TeamBuilder()
                learning_team = await team_builder.build_team(temp_config_path)
                team_runner = TeamRunner(learning_team)
                
                # Create session context
                session_context_dict = {
                    'team_identifier': temp_config_path,
                    'session_id': learning_session_id
                }
                
                # Use non-streaming run_team to preserve complete response formatting
                if console:
                    console.print(f"\n[bold blue]🎯 {learning_agent_config.get('name', 'LEARNING_AGENT').upper()}:[/bold blue]")
                    console.print("─" * 40)
                
                # Execute learning agent synchronously to preserve formatting
                team_result = await team_runner.run_team_async(
                    message="Please analyze the agent instructions and conversation history, then provide your response according to the format requirements.",
                    session_id=learning_session_id,
                    session_context=session_context_dict
                )
                
                # Extract the learning agent response from the complete result
                learning_agent_response = ""
                logger.info(f"DEBUG: Team result structure: {team_result}")
                logger.info(f"DEBUG: Team result keys: {list(team_result.keys()) if team_result else 'None'}")
                
                # New format: team_result has outputs with content
                if team_result and 'outputs' in team_result:
                    outputs = team_result['outputs']
                    logger.info(f"DEBUG: Found {len(outputs)} outputs in result")
                    for i, output in enumerate(outputs):
                        logger.info(f"DEBUG: Output {i}: type={output.get('type')}, content_length={len(str(output.get('content', '')))}")
                        if output.get('type') == 'completion' and output.get('content'):
                            learning_agent_response = output['content']
                            logger.info(f"DEBUG: Using output content: {repr(learning_agent_response[:200])}")
                            break
                else:
                    logger.info(f"DEBUG: No outputs found in result")
                
                # Display the complete response if console is available
                if console:
                    if learning_agent_response.strip():
                        # Show the complete formatted response
                        console.print(learning_agent_response)
                
                # Create result structure compatible with existing code
                results = team_result.get('result', {}).get('messages', [])
                
                if console:
                    console.print("\n")
                    console.print("┌" + "─" * 78 + "┐") 
                    console.print("│" + " " * 28 + "✨ COMPLETE ✨" + " " * 28 + "│")
                    console.print("└" + "─" * 78 + "┘")
                
                # Create result structure compatible with existing code
                result = {
                    'success': True,
                    'result': {'responses': results}
                }
                
                # Use the accumulated learning agent response from streaming (preserve formatting)
                content = learning_agent_response if learning_agent_response else ""
                
                # DEBUG: Log the raw response to understand formatting issues
                logger.info(f"DEBUG: Raw learning agent response length: {len(learning_agent_response)}")
                logger.info(f"DEBUG: Raw response repr: {repr(learning_agent_response[:500])}")
                logger.info(f"DEBUG: Stripped response repr: {repr(content[:500])}")
                
                # Handle quoted empty string/object response (agent indicating no changes)
                if content in ['""', "''", '', '{}', 'null']:
                    content = ""
                
                # Try to parse as JSON memory object
                updated_memory = None
                if content.strip():
                    try:
                        import json
                        updated_memory = json.loads(content.strip())
                        logger.info(f"Successfully parsed memory update: {updated_memory}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse memory as JSON: {e}, treating as no changes")
                        updated_memory = None
                
                # Determine if there are actual changes
                has_changes = updated_memory is not None and updated_memory != {}
                
                # Notify learning agent completion
                if progress_callback:
                    progress_callback.on_learning_agent_complete(target_agent_name, has_changes)
                
                if not has_changes:
                    logger.info(f"Learning agent recommended no memory changes for {target_agent_name}")
                    return None
                else:
                    logger.info(f"Learning agent provided updated memory for {target_agent_name}")
                    return updated_memory
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_config_path)
                except OSError:
                    pass
                
        except Exception as e:
            logger.error(f"Failed to execute learning agent: {e}")
            raise LearningError(f"Learning agent execution failed: {e}", "LEARNING_AGENT_ERROR")

