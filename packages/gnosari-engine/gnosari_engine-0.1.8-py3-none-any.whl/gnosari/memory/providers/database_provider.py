"""Database-based memory provider implementation."""

import json
import os
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ...schemas.learning import LearningError
from ...utils.logging import get_logger
from .base import MemoryProvider

logger = get_logger(__name__)


class DatabaseMemoryProvider(MemoryProvider):
    """Database-based memory provider implementation using SQLAlchemy."""
    
    def __init__(self, database_url: str):
        """Initialize database memory provider.
        
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
    
    async def get_agent_memory(self, team_path: str, agent_name: str) -> Optional[str]:
        """Retrieve agent memory from database.
        
        Args:
            team_path: Path to team configuration (used to derive team identifier)
            agent_name: Name of the agent
            
        Returns:
            Agent memory string or None if not found
        """
        try:
            team_identifier = self._extract_team_identifier(team_path)
            
            async with self.session_factory() as session:
                # Query agent table for memory column
                query = text("""
                    SELECT memory 
                    FROM agent 
                    WHERE identifier = :agent_name
                """)
                
                result = await session.execute(
                    query, 
                    {"team_id": team_identifier, "agent_name": agent_name}
                )
                row = result.fetchone()
                
                if row and row[0]:
                    # Return memory as string directly
                    return row[0] if isinstance(row[0], str) else str(row[0])
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get agent memory from database: {e}")
            raise LearningError(f"Database memory retrieval failed: {e}", "DATABASE_RETRIEVAL_ERROR")
    
    async def update_agent_memory(self, 
                                team_path: str, 
                                agent_name: str, 
                                new_memory: str) -> Optional[str]:
        """Update agent memory in database.
        
        Args:
            team_path: Path to team configuration (used to derive team identifier)
            agent_name: Name of the agent
            new_memory: New memory string to store
            
        Returns:
            None (no backup path for database operations)
        """
        try:
            team_identifier = self._extract_team_identifier(team_path)
            
            # Store memory as string directly
            memory_content = new_memory
            
            async with self.session_factory() as session:
                # Update agent memory using raw SQL for compatibility
                query = text("""
                    UPDATE agent 
                    SET memory = :memory_content,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE identifier = :agent_name
                """)
                
                result = await session.execute(
                    query, 
                    {
                        "memory_content": memory_content,
                        "team_id": team_identifier, 
                        "agent_name": agent_name
                    }
                )
                
                if result.rowcount == 0:
                    raise LearningError(
                        f"Agent {agent_name} not found in team {team_identifier}", 
                        "AGENT_NOT_FOUND"
                    )
                
                await session.commit()
                logger.info(f"Updated memory for agent {agent_name} in database")
                
                # Database operations don't create backup files
                return None
                
        except LearningError:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent memory in database: {e}")
            raise LearningError(f"Database memory update failed: {e}", "DATABASE_UPDATE_ERROR")
    
    async def validate_configuration(self, team_path: str) -> bool:
        """Validate database connection and team existence.
        
        Args:
            team_path: Path to team configuration (used to derive team identifier)
            
        Returns:
            True if database connection and team are valid
        """
        try:
            team_identifier = self._extract_team_identifier(team_path)
            
            async with self.session_factory() as session:
                # Check if team exists in database
                query = text("""
                    SELECT COUNT(*) 
                    FROM agent 
                    WHERE team_id = :team_id
                """)
                
                result = await session.execute(query, {"team_id": team_identifier})
                count = result.scalar()
                
                if count == 0:
                    raise LearningError(
                        f"No agents found for team {team_identifier} in database", 
                        "TEAM_NOT_FOUND"
                    )
                
                return True
                
        except LearningError:
            raise
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            raise LearningError(f"Database validation failed: {e}", "DATABASE_VALIDATION_ERROR")
    
    def _extract_team_identifier(self, team_path: str) -> str:
        """Extract team identifier from team path.
        
        For database operations, we need a consistent team identifier.
        This could be derived from the team path or configuration.
        
        Args:
            team_path: Path to team configuration
            
        Returns:
            Team identifier string
        """
        from pathlib import Path
        
        try:
            path = Path(team_path)
            
            if path.is_file():
                # For monolithic files, use filename without extension
                return path.stem
            elif path.is_dir():
                # For modular configs, use directory name
                return path.name
            else:
                # Fallback to the path string itself
                return str(path)
                
        except Exception:
            # Ultimate fallback
            return str(team_path).replace("/", "_").replace("\\", "_")
    
    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()