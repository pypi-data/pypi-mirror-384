import os
from typing import Optional
from ..processors.enhanced_learning_processor import EnhancedMemoryLearningProcessor
from ..repositories.learning_session_repository import DatabaseLearningSessionRepository
from ..session_services.learning_session_service import LearningSessionService
from ..learning_processor import MemoryLearningProcessorFactory
from ...utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedMemoryLearningProcessorFactory(MemoryLearningProcessorFactory):
    """Factory for creating enhanced memory learning processor with session storage."""
    
    @staticmethod
    def create_processor(database_url: Optional[str] = None, 
                        progress_callback = None,
                        enable_session_storage: bool = True,
                        session_storage_database_url: Optional[str] = None) -> EnhancedMemoryLearningProcessor:
        """Create enhanced memory learning processor with session storage.
        
        Args:
            database_url: Database URL for session retrieval
            progress_callback: Optional progress callback
            enable_session_storage: Whether to enable session storage
            session_storage_database_url: Database URL for session storage (defaults to database_url)
            
        Returns:
            Configured EnhancedMemoryLearningProcessor instance
        """
        # Create base dependencies using parent factory
        base_processor = MemoryLearningProcessorFactory.create_processor(database_url, progress_callback)
        
        # Create session storage service if enabled
        learning_session_service = None
        if enable_session_storage:
            storage_db_url = (session_storage_database_url or 
                            database_url or 
                            os.getenv('LEARNING_SESSION_DATABASE_URL') or
                            os.getenv('GNOSARI_DATABASE_URL') or
                            os.getenv('SESSION_DATABASE_URL'))
            
            if storage_db_url:
                try:
                    repository = DatabaseLearningSessionRepository(storage_db_url)
                    learning_session_service = LearningSessionService(repository)
                    logger.info("Learning session storage enabled")
                except Exception as e:
                    logger.warning(f"Failed to create learning session service: {e}")
            else:
                logger.info("Learning session storage disabled - no database URL configured")
        
        return EnhancedMemoryLearningProcessor(
            session_retriever=base_processor.session_retriever,
            learning_executor=base_processor.learning_executor,
            memory_updater=base_processor.memory_updater,
            progress_reporter=base_processor.progress_reporter,
            learning_session_service=learning_session_service
        )