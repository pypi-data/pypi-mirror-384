from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from ..dtos.learning_session_dto import LearningSessionData
from ...schemas.learning import LearningError
from ...utils.logging import get_logger

logger = get_logger(__name__)


class LearningSessionRepository(ABC):
    """Abstract repository for learning session operations."""
    
    @abstractmethod
    async def create_learning_session(self, session_data: LearningSessionData) -> None:
        """Create a new learning session record."""
        pass
    
    @abstractmethod
    async def get_learning_session_by_session_id(self, session_id: str, account_id: int) -> Optional[Dict[str, Any]]:
        """Get learning session by session_id and account_id."""
        pass


class DatabaseLearningSessionRepository(LearningSessionRepository):
    """Database implementation of learning session repository."""
    
    def __init__(self, database_url: str):
        """Initialize database repository.
        
        Args:
            database_url: Database connection URL (e.g., postgresql+asyncpg://...)
        """
        self.database_url = database_url
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """Get or create database engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True
            )
        return self._engine
    
    @property 
    def session_factory(self):
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._session_factory
    
    async def create_learning_session(self, session_data: LearningSessionData) -> None:
        """Create a new learning session record."""
        try:
            async with self.session_factory() as session:
                query = text("""
                    INSERT INTO learning_session 
                    (team_id, agent_id, team_identifier, agent_identifier, session_id, 
                     previous_memory, updated_memory, has_changes, learning_summary, confidence_score, account_id, created_at, updated_at)
                    VALUES 
                    (:team_id, :agent_id, :team_identifier, :agent_identifier, :session_id,
                     :previous_memory, :updated_memory, :has_changes, :learning_summary, :confidence_score, :account_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """)
                
                await session.execute(query, session_data.model_dump())
                await session.commit()
                logger.info(f"Created learning session with session_id: {session_data.session_id}")
                
        except Exception as e:
            logger.error(f"Failed to create learning session: {e}")
            raise LearningError(f"Learning session storage failed: {e}", "STORAGE_ERROR")
    
    async def get_learning_session_by_session_id(self, session_id: str, account_id: int) -> Optional[Dict[str, Any]]:
        """Get learning session by session_id and account_id."""
        try:
            async with self.session_factory() as session:
                query = text("""
                    SELECT team_id, agent_id, team_identifier, agent_identifier, session_id,
                           previous_memory, updated_memory, has_changes, learning_summary, 
                           confidence_score, account_id, created_at, updated_at
                    FROM learning_session 
                    WHERE session_id = :session_id AND account_id = :account_id
                """)
                
                result = await session.execute(query, {
                    "session_id": session_id,
                    "account_id": account_id
                })
                
                row = result.fetchone()
                if row:
                    return {
                        "team_id": row[0],
                        "agent_id": row[1],
                        "team_identifier": row[2],
                        "agent_identifier": row[3],
                        "session_id": row[4],
                        "previous_memory": row[5],
                        "updated_memory": row[6],
                        "has_changes": row[7],
                        "learning_summary": row[8],
                        "confidence_score": row[9],
                        "account_id": row[10],
                        "created_at": row[11],
                        "updated_at": row[12]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get learning session: {e}")
            raise LearningError(f"Learning session retrieval failed: {e}", "RETRIEVAL_ERROR")
    
    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()