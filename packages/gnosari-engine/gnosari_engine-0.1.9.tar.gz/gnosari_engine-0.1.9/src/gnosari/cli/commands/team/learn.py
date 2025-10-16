"""Learn command implementation for team learning system."""

import asyncio
import logging
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

# Load environment variables at module level
from ...utils import load_environment_variables
load_environment_variables()

from ....schemas.learning import (
    LearningRequest, 
    LearningResponse, 
    LearningError,
    SessionContext as LearningSessionContext
)
from ....schemas.session import SessionContext
from ....engine.learning_processor import LearningProcessor, LearningProgressCallback
from ....engine.queue_manager import QueueManager
from ....memory.factory import create_memory_manager
from ....memory.repositories.learning_session_repository import DatabaseLearningSessionRepository
from ....memory.session_services.learning_session_service import LearningSessionService
from ....utils.logging import get_logger

logger = get_logger(__name__)


class LearnCommandResult:
    """Result of learn command execution."""
    
    def __init__(self, success: bool, message: str, results: Optional[List[LearningResponse]] = None):
        self.success = success
        self.message = message
        self.results = results or []


class LearnCommand:
    """Command handler for team learning operations."""
    
    def __init__(self, console=None):
        """Initialize learn command.
        
        Args:
            console: Rich console for output (optional)
        """
        self.console = console
        self._learning_processor = None
        self._learning_session_service = None
    
    def _create_progress_callback(self) -> Optional[LearningProgressCallback]:
        """Create progress callback for formatted console output."""
        if not self.console:
            return None
        
        class ProgressCallback:
            def __init__(self, console):
                self.console = console
                self.current_agent = None
            
            def on_session_retrieval_start(self, agent_name: str, team_identifier: str) -> None:
                """Called when session retrieval starts for an agent."""
                if self.current_agent != agent_name:
                    self.current_agent = agent_name
                    self.console.print(f"\n[bold blue]🎯 {agent_name.upper()}:[/bold blue]")
                    self.console.print("─" * 40)
                
                self.console.print(f"[dim yellow]📊 Retrieving sessions from team '{team_identifier}'...[/dim yellow]")
            
            def on_sessions_retrieved(self, agent_name: str, session_count: int, time_period: str) -> None:
                """Called when sessions are successfully retrieved."""
                if session_count > 0:
                    self.console.print(f"[green]✅ Found {session_count} sessions ({time_period})[/green]")
                else:
                    self.console.print(f"[yellow]⚠️  No sessions found for analysis[/yellow]")
            
            def on_learning_agent_start(self, agent_name: str, learning_session_id: str) -> None:
                """Called when learning agent execution starts."""
                self.console.print(f"[dim yellow]🤖 Starting learning agent analysis...[/dim yellow]")
                self.console.print(f"[dim]Session: {learning_session_id}[/dim]")
                self.console.print()
                # Visual separator is now handled by streaming logic
                self.console.print("┌" + "─" * 78 + "┐")
                self.console.print("│" + " " * 25 + "🧠 LEARNING AGENT" + " " * 25 + "│")
                self.console.print("└" + "─" * 78 + "┘")
                self.console.print()
            
            def on_learning_agent_complete(self, agent_name: str, has_changes: bool) -> None:
                """Called when learning agent execution completes."""
                # Completion separator is now handled by streaming logic
                pass
            
            def on_instructions_updated(self, agent_name: str, backup_path: str) -> None:
                """Called when agent memory is successfully updated."""
                self.console.print(f"[green]💾 Memory updated successfully[/green]")
                if backup_path:
                    self.console.print(f"[dim]Backup created: {backup_path}[/dim]")
        
        return ProgressCallback(self.console)
    
    def _load_team_config(self, team_path: str) -> Optional[Dict[str, Any]]:
        """Load team configuration to check for account_id.
        
        Args:
            team_path: Path to team configuration file or directory
            
        Returns:
            Team configuration dictionary or None if loading fails
        """
        try:
            import yaml
            from pathlib import Path
            
            path = Path(team_path)
            
            if path.is_file():
                # Monolithic YAML file
                with open(path) as f:
                    return yaml.safe_load(f)
            elif path.is_dir():
                # Modular configuration - load main.yaml
                main_file = path / "main.yaml"
                if main_file.exists():
                    with open(main_file) as f:
                        return yaml.safe_load(f)
                else:
                    logger.warning(f"No main.yaml found in modular config directory: {path}")
                    return {}
            else:
                logger.warning(f"Team path does not exist: {team_path}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to load team configuration: {e}")
            return None
    
    def _create_session_context(self, team_config: Dict[str, Any], team_path: str) -> Optional[SessionContext]:
        """Create session context if account_id is present in team configuration.
        
        Args:
            team_config: Team configuration dictionary
            team_path: Path to team configuration
            
        Returns:
            SessionContext if account_id is found, None otherwise
        """
        if not team_config:
            return None
        
        account_id = team_config.get('account_id')
        if account_id is None:
            logger.debug("No account_id found in team configuration - learning sessions will not be stored")
            return None
        
        from datetime import datetime
        from pathlib import Path
        
        team_identifier = team_config.get('id', Path(team_path).stem)
        session_id = f"learning-{team_identifier}-{datetime.utcnow().isoformat()}"
        
        logger.debug(f"Creating session context with account_id: {account_id}")
        
        return SessionContext(
            account_id=account_id,
            team_identifier=team_identifier,
            session_id=session_id,
            original_config=team_config
        )
    
    async def run(self, args) -> LearnCommandResult:
        """Execute learn command.
        
        Args:
            args: Command arguments with team_path, agent, mode, wait
            
        Returns:
            LearnCommandResult with execution results
        """
        try:
            # Validate arguments
            if not hasattr(args, 'team_path') or not args.team_path:
                return LearnCommandResult(False, "Team path is required")
            
            team_path = args.team_path
            agent_name = getattr(args, 'agent', None)
            execution_mode = getattr(args, 'mode', 'sync')
            wait_for_completion = getattr(args, 'wait', False)
            team_wide_learning = getattr(args, 'team_wide', False)
            
            # Validate team path exists
            if not Path(team_path).exists():
                return LearnCommandResult(False, f"Team path does not exist: {team_path}")
            
            # Load team configuration to check for account_id
            team_config = self._load_team_config(team_path)
            session_context = self._create_session_context(team_config, team_path) if team_config else None
            
            # Create learning processor
            learning_processor = await self._get_learning_processor()
            
            # Create learning request
            request = LearningRequest(
                team_path=team_path,
                target_agents=[agent_name] if agent_name else None,
                execution_mode=execution_mode,
                team_wide_learning=team_wide_learning
            )
            
            # Execute learning based on mode
            if execution_mode == 'sync':
                return await self._execute_sync_learning(learning_processor, request, team_config, session_context)
            else:
                return await self._execute_async_learning(learning_processor, request, wait_for_completion)
                
        except LearningError as e:
            logger.error(f"Learning error: {e}")
            return LearnCommandResult(False, f"Learning failed: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error in learn command: {e}")
            return LearnCommandResult(False, f"Command failed: {str(e)}")
    
    async def _execute_sync_learning(self, 
                                   learning_processor: LearningProcessor, 
                                   request: LearningRequest,
                                   team_config: Optional[Dict[str, Any]] = None,
                                   session_context: Optional[SessionContext] = None) -> LearnCommandResult:
        """Execute synchronous learning."""
        try:
            if self.console:
                self.console.print("[yellow]Starting synchronous learning...[/yellow]")
            
            # Create progress callback for formatted output
            progress_callback = self._create_progress_callback()
            
            results = await learning_processor.process_learning_sync(request, progress_callback=progress_callback)
            
            # Store learning sessions if account_id is present and service is available
            await self._store_learning_sessions(results, team_config, session_context)
            
            # Format results
            success_count = sum(1 for r in results if r.has_changes)
            total_count = len(results)
            
            if success_count == 0:
                message = f"Learning completed for {total_count} agents - no changes recommended"
            else:
                message = f"Learning completed - {success_count}/{total_count} agents updated"
            
            if self.console:
                self._display_sync_results(results)
            
            return LearnCommandResult(True, message, results)
            
        except Exception as e:
            logger.error(f"Sync learning failed: {e}")
            return LearnCommandResult(False, f"Synchronous learning failed: {str(e)}")
    
    async def _execute_async_learning(self, 
                                    learning_processor: LearningProcessor, 
                                    request: LearningRequest,
                                    wait_for_completion: bool) -> LearnCommandResult:
        """Execute asynchronous learning."""
        try:
            if self.console:
                self.console.print("[yellow]Starting asynchronous learning...[/yellow]")
            
            task_ids = await learning_processor.process_learning_async(request)
            
            if not task_ids:
                return LearnCommandResult(False, "No learning tasks were queued")
            
            if self.console:
                self.console.print(f"[green]Queued {len(task_ids)} learning tasks[/green]")
                for i, task_id in enumerate(task_ids, 1):
                    self.console.print(f"  {i}. Task ID: {task_id}")
            
            if wait_for_completion:
                return await self._wait_for_async_completion(learning_processor, task_ids)
            else:
                message = f"Learning tasks queued successfully. Task IDs: {', '.join(task_ids)}"
                return LearnCommandResult(True, message)
                
        except Exception as e:
            logger.error(f"Async learning failed: {e}")
            return LearnCommandResult(False, f"Asynchronous learning failed: {str(e)}")
    
    async def _wait_for_async_completion(self, 
                                       learning_processor: LearningProcessor, 
                                       task_ids: List[str]) -> LearnCommandResult:
        """Wait for async tasks to complete."""
        try:
            if self.console:
                self.console.print("[yellow]Waiting for learning tasks to complete...[/yellow]")
            
            results = await learning_processor.wait_for_learning_completion(task_ids, timeout=300)
            
            # Format results
            success_count = sum(1 for r in results if r.has_changes)
            total_count = len(results)
            
            if success_count == 0:
                message = f"Learning completed for {total_count} agents - no changes recommended"
            else:
                message = f"Learning completed - {success_count}/{total_count} agents updated"
            
            if self.console:
                self._display_sync_results(results)
            
            return LearnCommandResult(True, message, results)
            
        except Exception as e:
            logger.error(f"Failed to wait for async completion: {e}")
            return LearnCommandResult(False, f"Failed to wait for completion: {str(e)}")
    
    def _display_sync_results(self, results: List[LearningResponse]) -> None:
        """Display synchronous learning results."""
        if not self.console:
            return
        
        self.console.print("\n[bold]Learning Results:[/bold]")
        
        for result in results:
            if result.has_changes:
                self.console.print(f"  ✅ [green]{result.agent_name}[/green]: {result.learning_summary}")
                if result.confidence_score:
                    self.console.print(f"     Confidence: {result.confidence_score:.1%}")
            else:
                self.console.print(f"  ⏭️  [yellow]{result.agent_name}[/yellow]: {result.learning_summary}")
        
        self.console.print("")
    
    async def _process_learning_with_enhanced_processor(self, 
                                                      learning_processor, 
                                                      request: LearningRequest,
                                                      session_context: Optional[SessionContext] = None) -> List[LearningResponse]:
        """Process learning using the enhanced processor with session storage support.
        
        Args:
            learning_processor: Enhanced memory learning processor
            request: Learning request
            session_context: Optional session context for storage
            
        Returns:
            List of learning responses
        """
        import yaml
        from pathlib import Path
        from ....schemas.learning import LearningConfig
        
        results = []
        
        try:
            # Load team configuration
            team_config = self._load_team_config(request.team_path)
            if not team_config:
                raise LearningError("Failed to load team configuration", "CONFIG_LOAD_ERROR")
            
            # Extract learning configuration
            learning_config_data = team_config.get('learning', {})
            if not learning_config_data:
                raise LearningError("No learning configuration found in team", "NO_LEARNING_CONFIG")
            
            learning_config = LearningConfig(**learning_config_data)
            if not learning_config.enabled:
                raise LearningError("Learning is disabled for this team", "LEARNING_DISABLED")
            
            # Determine target agents
            target_agents = request.target_agents
            if not target_agents:
                # Get all agents from config
                agents = team_config.get('agents', [])
                target_agents = []
                for agent in agents:
                    agent_id = agent.get('id') or agent.get('name', '').lower().replace(' ', '_')
                    if agent_id != learning_config.learning_agent:  # Don't learn the learning agent
                        target_agents.append(agent_id)
            
            if not target_agents:
                logger.warning("No target agents found for learning")
                return []
            
            # Process each agent individually
            for agent_name in target_agents:
                try:
                    if self.console:
                        self.console.print(f"\n[bold blue]🎯 {agent_name.upper()}:[/bold blue]")
                        self.console.print("─" * 40)
                    
                    # Process learning for this agent
                    result = await learning_processor.process_agent_learning(
                        team_path=request.team_path,
                        agent_name=agent_name,
                        team_config=team_config,
                        learning_config=learning_config,
                        team_wide_learning=request.team_wide_learning,
                        session_context=session_context
                    )
                    
                    results.append(result)
                    
                    if self.console:
                        if result.has_changes:
                            self.console.print(f"[green]✅ Memory updated: {result.learning_summary}[/green]")
                        else:
                            self.console.print(f"[yellow]ℹ️  No changes: {result.learning_summary}[/yellow]")
                
                except Exception as e:
                    logger.error(f"Learning failed for agent {agent_name}: {e}")
                    # Create error response
                    error_result = LearningResponse(
                        agent_name=agent_name,
                        original_memory="",
                        updated_memory=None,
                        has_changes=False,
                        learning_summary=f"Learning failed: {str(e)}",
                        confidence_score=0.0
                    )
                    results.append(error_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Enhanced learning processing failed: {e}")
            raise LearningError(f"Learning processing failed: {e}", "ENHANCED_LEARNING_ERROR")
    
    async def _get_learning_processor(self) -> LearningProcessor:
        """Get or create learning processor instance."""
        if self._learning_processor is None:
            # Get database URL for session storage
            database_url = self._get_database_url() or "sqlite+aiosqlite:///conversations.db"
            
            # Create queue manager (optional for sync mode)
            queue_manager = None
            try:
                queue_manager = await self._create_queue_manager()
            except Exception as e:
                logger.warning(f"Queue manager not available: {e}")
            
            # Create memory manager using environment configuration
            memory_manager = self._create_memory_manager()
            
            self._learning_processor = LearningProcessor(
                database_url=database_url, 
                queue_manager=queue_manager,
                memory_manager=memory_manager
            )
        
        return self._learning_processor
    
    def _get_learning_session_service(self) -> Optional[LearningSessionService]:
        """Get or create learning session service if database is available."""
        if self._learning_session_service is None:
            try:
                # Get database URL - try various environment variables
                database_url = (
                    os.getenv('LEARNING_SESSION_DATABASE_URL') or 
                    self._get_database_url() or
                    os.getenv('GNOSARI_DATABASE_URL')
                )
                
                if database_url:
                    repository = DatabaseLearningSessionRepository(database_url)
                    self._learning_session_service = LearningSessionService(repository)
                    logger.debug("Learning session service created successfully")
                else:
                    logger.debug("No database URL available for learning session storage")
                    
            except Exception as e:
                logger.warning(f"Failed to create learning session service: {e}")
                
        return self._learning_session_service
    
    async def _store_learning_sessions(self, 
                                     results: List[LearningResponse], 
                                     team_config: Optional[Dict[str, Any]], 
                                     session_context: Optional[SessionContext]) -> None:
        """Store learning sessions in database if conditions are met."""
        learning_session_service = self._get_learning_session_service()
        
        if not learning_session_service or not team_config or not session_context:
            return
        
        try:
            # Create a learning context for the storage service
            from ....schemas.learning import LearningContext, LearningConfig
            
            # Extract learning config from team config
            learning_config_data = team_config.get('learning', {})
            if not learning_config_data:
                logger.debug("No learning configuration found, skipping session storage")
                return
            
            learning_config = LearningConfig(**learning_config_data)
            learning_context = LearningContext(
                team_identifier=team_config.get('id', 'unknown'),
                agent_names=[r.agent_name for r in results],
                session_filters={},
                learning_config=learning_config,
                session_count=None,
                time_period=None,
                execution_mode=learning_config.execution_mode,
                team_path=None
            )
            
            # Store each learning result as a session
            for result in results:
                try:
                    # Create a session context specific to this agent
                    agent_session_context = SessionContext(
                        account_id=session_context.account_id,
                        team_id=session_context.team_id,
                        agent_id=session_context.agent_id,
                        team_identifier=session_context.team_identifier,
                        agent_identifier=result.agent_name,
                        session_id=f"{session_context.session_id}-{result.agent_name}",
                        original_config=session_context.original_config,
                        metadata=session_context.metadata
                    )
                    
                    await learning_session_service.store_learning_session(
                        result, learning_context, team_config, agent_session_context
                    )
                    logger.info(f"Stored learning session for agent {result.agent_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to store learning session for {result.agent_name}: {e}")
                    # Continue with other agents
                    
        except Exception as e:
            logger.warning(f"Failed to store learning sessions: {e}")
    
    def _create_memory_manager(self):
        """Create memory manager using environment configuration."""
        import os
        
        # Get memory provider configuration from environment
        provider_type = os.getenv('LEARNING_PROVIDER', 'yaml').lower()
        database_url = os.getenv('LEARNING_DATABASE_URL')
        backup_enabled = os.getenv('LEARNING_BACKUP_ENABLED', 'true').lower() == 'true'
        
        # Create memory manager with environment configuration
        memory_manager = create_memory_manager(
            provider_type=provider_type,
            database_url=database_url,
            backup_enabled=backup_enabled
        )
        
        if self.console:
            provider_name = "Database" if provider_type == "database" else "YAML"
            self.console.print(f"[dim]Using {provider_name} memory provider[/dim]")
            if provider_type == "database" and database_url:
                # Mask sensitive parts of the URL for display
                display_url = database_url.split('@')[-1] if '@' in database_url else database_url
                self.console.print(f"[dim]Database: {display_url}[/dim]")
        
        return memory_manager
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL from environment or configuration."""
        import os
        # Check for session database URL first, then fallback to general database URL
        return (os.getenv('SESSION_DATABASE_URL') or 
                os.getenv('GNOSARI_DATABASE_URL'))
    
    def _get_api_url(self) -> Optional[str]:
        """Get API URL from environment or configuration."""
        import os
        return os.getenv('GNOSARI_API_URL')
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or configuration."""
        import os
        return os.getenv('GNOSARI_API_KEY')
    
    async def _create_queue_manager(self) -> Optional[QueueManager]:
        """Create queue manager if dependencies are available."""
        try:
            import redis.asyncio as redis
            from celery import Celery
            
            # Create Redis client
            redis_url = self._get_redis_url()
            if not redis_url:
                return None
            
            redis_client = redis.from_url(redis_url)
            
            # Create Celery app
            celery_app = Celery('gnosari_learning')
            celery_app.conf.update(
                broker_url=redis_url,
                result_backend=redis_url,
                task_serializer='json',
                accept_content=['json'],
                result_serializer='json',
                timezone='UTC',
                enable_utc=True,
            )
            
            return QueueManager(celery_app, redis_client)
            
        except ImportError as e:
            logger.warning(f"Queue dependencies not available: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to create queue manager: {e}")
            return None
    
    def _get_redis_url(self) -> Optional[str]:
        """Get Redis URL from environment."""
        import os
        return os.getenv('REDIS_URL', os.getenv('CELERY_BROKER_URL'))