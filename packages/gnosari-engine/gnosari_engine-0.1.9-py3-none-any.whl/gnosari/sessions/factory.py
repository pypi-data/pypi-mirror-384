"""
Factory function for creating session implementations
"""

import logging
import os
from typing import Optional, Dict, Any
from agents.memory.session import SessionABC

from .database import DatabaseSession
from .api import ApiSession
from ..schemas import SessionContext

logger = logging.getLogger(__name__)


def GnosariContextSession(session_id: str, 
                         session_context: Optional[SessionContext] = None) -> SessionABC:
    """Factory function that creates the appropriate session type based on configuration.
    
    Args:
        session_id: Unique identifier for the conversation
        session_context: SessionContext object containing account_id, team_id, agent_id
    
    Returns:
        SessionABC: Appropriate session implementation (ApiSession or DatabaseSession)
    """
    # Get session configuration
    session_provider = os.getenv("SESSION_PROVIDER", "file").lower()
    session_database_url = os.getenv("SESSION_DATABASE_URL")
    
    # Check for API-based session
    if session_provider == "gnosari_api":
        api_base_url = os.getenv("GNOSARI_API_BASE_URL")
        api_key = os.getenv("GNOSARI_API_KEY")
        
        if api_base_url and api_key and session_context and session_context.account_id:
            try:
                import aiohttp
                logger.info(f"Using Gnosari API session storage: {api_base_url}")
                return ApiSession(
                    session_id=session_id,
                    session_context=session_context,
                    api_base_url=api_base_url,
                    api_key=api_key
                )
            except ImportError:
                logger.warning("aiohttp not available for API session, falling back to database")
                session_provider = "file"
            except ValueError as e:
                logger.warning(f"Invalid API configuration: {e}, falling back to database")
                session_provider = "file"
        else:
            logger.warning("Missing API configuration or account_id, falling back to database")
            session_provider = "file"
    
    # Use database session (file or external database)
    if session_provider == "file":
        database_url = session_database_url or "sqlite+aiosqlite:///conversations.db"
        create_tables = True
    elif session_provider == "database":
        if not session_database_url:
            raise ValueError("SESSION_DATABASE_URL is required when SESSION_PROVIDER is 'database'")
        database_url = session_database_url
        # For SQLite databases, always allow table creation for development/testing
        create_tables = "sqlite" in session_database_url.lower()
    else:
        # Default to file for unknown providers
        logger.warning(f"Unknown session provider '{session_provider}', defaulting to file")
        database_url = "sqlite+aiosqlite:///conversations.db"
        create_tables = True
    
    logger.info(f"Using database session storage: {database_url}")
    return DatabaseSession(
        session_id=session_id,
        session_context=session_context,
        database_url=database_url,
        create_tables=create_tables
    )