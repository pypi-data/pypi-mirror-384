"""Team learning tool for triggering learning system operations."""

import asyncio
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field

from ...schemas.base import BaseTool
from ...schemas.learning import LearningToolInput, LearningToolOutput, LearningRequest
from ...engine.learning_processor import LearningProcessor
from ...engine.queue_manager import QueueManager
from ...utils.logging import get_logger

logger = get_logger(__name__)


class TeamLearningTool(BaseTool[LearningToolInput, LearningToolOutput]):
    """Tool for triggering team learning operations."""
    
    def __init__(self, config=None):
        """Initialize team learning tool."""
        super().__init__(config or {})
        self._learning_processor = None
    
    async def run(self, params: LearningToolInput) -> LearningToolOutput:
        """Execute team learning operation.
        
        Args:
            params: Learning tool input parameters
            
        Returns:
            Learning tool output with results
        """
        try:
            logger.info(f"Starting team learning for: {params.team_path}")
            
            # Get or create learning processor
            learning_processor = await self._get_learning_processor()
            
            # Create learning request
            request = LearningRequest(
                team_path=params.team_path,
                target_agents=[params.agent_name] if params.agent_name else None,
                execution_mode=params.execution_mode
            )
            
            # Execute learning based on mode
            if params.execution_mode == "sync":
                results = await learning_processor.process_learning_sync(request)
                
                # Format results
                success_count = sum(1 for r in results if r.has_changes)
                total_count = len(results)
                
                if success_count == 0:
                    message = f"Learning completed for {total_count} agents - no changes recommended"
                else:
                    message = f"Learning completed - {success_count}/{total_count} agents updated"
                
                return LearningToolOutput(
                    success=True,
                    message=message,
                    results=results
                )
                
            else:  # async mode
                task_ids = await learning_processor.process_learning_async(request)
                
                if params.wait_for_completion:
                    # Wait for completion
                    results = await learning_processor.wait_for_learning_completion(task_ids, timeout=300)
                    
                    success_count = sum(1 for r in results if r.has_changes)
                    total_count = len(results)
                    
                    if success_count == 0:
                        message = f"Learning completed for {total_count} agents - no changes recommended"
                    else:
                        message = f"Learning completed - {success_count}/{total_count} agents updated"
                    
                    return LearningToolOutput(
                        success=True,
                        message=message,
                        results=results
                    )
                else:
                    # Return task IDs for monitoring
                    return LearningToolOutput(
                        success=True,
                        message=f"Learning tasks queued successfully. {len(task_ids)} tasks in progress.",
                        task_ids=task_ids
                    )
                    
        except Exception as e:
            logger.error(f"Team learning failed: {e}")
            return LearningToolOutput(
                success=False,
                message=f"Learning operation failed: {str(e)}",
                error_details={"error": str(e), "type": type(e).__name__}
            )
    
    async def _get_learning_processor(self) -> LearningProcessor:
        """Get or create learning processor instance."""
        if self._learning_processor is None:
            # Get database URL
            database_url = self._get_database_url() or "sqlite+aiosqlite:///conversations.db"
            
            # Create queue manager (optional for sync mode)
            queue_manager = None
            try:
                queue_manager = await self._create_queue_manager()
            except Exception as e:
                logger.warning(f"Queue manager not available: {e}")
            
            self._learning_processor = LearningProcessor(database_url, queue_manager)
        
        return self._learning_processor
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL from environment or configuration."""
        import os
        return os.getenv('GNOSARI_DATABASE_URL')
    
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
    
    @property 
    def tool_name(self) -> str:
        """Tool name for registration."""
        return "team_learning"
    
    @property
    def tool_description(self) -> str:
        """Tool description for agents."""
        return "Trigger learning for team agents based on session history to improve their performance"