"""
Database session implementation using SQLAlchemy
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from agents.memory.session import SessionABC
from agents.items import TResponseInputItem
from ..schemas import SessionContext

# SQLAlchemy imports for database implementation
from sqlalchemy import (
    DateTime, Column, ForeignKey, Index, Integer, MetaData, String, Table, Text,
    delete, insert, select, text as sql_text, update
)
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


class DatabaseSession(SessionABC):
    """Database session implementation using SQLAlchemy."""

    _metadata: MetaData
    _sessions: Table
    _messages: Table

    def __init__(self, 
                 session_id: str, 
                 session_context: Optional[SessionContext] = None,
                 database_url: Optional[str] = None,
                 create_tables: bool = True):
        """Initialize database session.
        
        Args:
            session_id: Unique identifier for the conversation
            session_context: SessionContext object containing account_id (int), team_id (str), agent_id (str)
            database_url: Database URL, defaults to SQLite file
            create_tables: Whether to create tables if they don't exist
        """
        self.session_id = session_id
        self._session_context_obj = session_context
        
        # Convert SessionContext to dictionary for internal use
        if session_context is not None:
            self.session_context = session_context.model_dump(exclude_none=True)
        else:
            self.session_context = {}
        self._lock = asyncio.Lock()
        
        # Set default database URL if not provided
        self._database_url = database_url or "sqlite+aiosqlite:///conversations.db"
        self._create_tables = create_tables
        
        # Initialize database engine with robust connection handling
        self._database_available = True
        try:
            self._engine = create_async_engine(
                self._database_url,
                pool_size=20,  # Increased from default 5
                max_overflow=30,  # Increased from default 10
                pool_timeout=30,  # 30 seconds timeout for getting connection from pool
                pool_recycle=3600,  # Recycle connections every hour
                pool_pre_ping=True,  # Validate connections before use
                connect_args=self._get_connect_args()
            )
            self._setup_database_schema()
            logger.info(f"Database engine initialized successfully: {self._database_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            self._database_available = False
            self._engine = None
            # Don't raise here - we'll handle it gracefully in operations
        
        logger.info(f"Initialized DatabaseSession for session_id: {session_id}, context: {session_context}")
    
    async def cleanup(self):
        """Clean up database connections and resources."""
        if hasattr(self, '_engine') and self._engine:
            try:
                await self._engine.dispose()
                logger.debug(f"Disposed database engine for session {self.session_id}")
            except Exception as e:
                logger.warning(f"Error disposing database engine: {e}")
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        if hasattr(self, '_engine') and self._engine:
            logger.warning(f"Session {self.session_id} was not properly cleaned up - engine still active")
    
    def _get_connect_args(self):
        """Get database-specific connection arguments."""
        connect_args = {}
        
        if "sqlite" in self._database_url:
            connect_args["timeout"] = 30
        elif "mysql" in self._database_url:
            connect_args["command_timeout"] = 30
        elif "postgresql" in self._database_url:
            connect_args["server_settings"] = {"statement_timeout": "30s"}
        
        return connect_args
    
    def _setup_database_schema(self):
        """Set up database schema using existing python-api models structure."""
        self._metadata = MetaData()
        
        # Sessions table - compatible with python-api schema
        self._sessions = Table(
            "sessions",
            self._metadata,
            Column("session_id", String, primary_key=True),
            Column("account_id", Integer, nullable=True),  # Account ID from YAML or external source
            Column("team_id", Integer, nullable=True),     # Integer team ID (references teams table in python-api)
            Column("agent_id", Integer, nullable=True),    # Integer agent ID (references agents table in python-api)
            Column("team_identifier", String, nullable=True),   # Team identifier from YAML 'id' field 
            Column("agent_identifier", String, nullable=True),  # Agent identifier from YAML agents[].id field
            Column("created_at", DateTime, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP")),  # From TimestampMixin
            Column("updated_at", DateTime, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"), onupdate=sql_text("CURRENT_TIMESTAMP")),  # From TimestampMixin
        )

        # Messages table - engine-compatible  
        self._messages = Table(
            "session_messages",  # Correct table name from python-api
            self._metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("session_id", String, ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False),
            Column("message_data", Text, nullable=False),
            Column("account_id", Integer, nullable=True),  # Account ID from session context
            Column("created_at", DateTime, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP")),  # From TimestampMixin
            Column("updated_at", DateTime, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"), onupdate=sql_text("CURRENT_TIMESTAMP")),  # From TimestampMixin
            Index("idx_session_messages_session_time", "session_id", "created_at"),  # Match python-api index name
            sqlite_autoincrement=True,
        )

        # Async session factory with proper connection handling
        self._session_factory = async_sessionmaker(
            self._engine, 
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
    
    async def _ensure_tables(self) -> None:
        """Ensure tables are created before any database operations."""
        logger.debug(f"_ensure_tables called for session {self.session_id}, database_available: {self._database_available}, create_tables: {self._create_tables}")
        
        if not self._database_available:
            logger.error(f"Database is not available for session {self.session_id}")
            raise RuntimeError("Database is not available")
            
        if self._create_tables:
            try:
                logger.info(f"Creating database tables for session {self.session_id}")
                async with self._engine.begin() as conn:
                    await conn.run_sync(self._metadata.create_all)
                self._create_tables = False  # Only create once
                logger.info(f"Database tables created successfully for session {self.session_id}")
            except Exception as e:
                logger.error(f"Failed to create database tables: {e}")
                self._database_available = False
                raise
        else:
            logger.debug(f"Tables already created for session {self.session_id}")
    
    async def _serialize_item(self, item: TResponseInputItem) -> str:
        """Serialize an item to JSON string, preserving reasoning items."""
        try:
            # First try to use the item's built-in serialization if available
            if hasattr(item, 'model_dump') or hasattr(item, 'dict'):
                if hasattr(item, 'model_dump'):
                    return json.dumps(item.model_dump(), separators=(",", ":"))
                else:
                    return json.dumps(item.dict(), separators=(",", ":"))
            else:
                # Fall back to standard JSON serialization
                return json.dumps(item, separators=(",", ":"))
        except (TypeError, AttributeError) as e:
            logger.warning(f"Failed to serialize item properly: {e}, using string representation")
            return json.dumps(str(item), separators=(",", ":"))

    async def get_items(self, limit: int | None = None) -> List[TResponseInputItem]:
        """Retrieve conversation history for this session."""
        if not self._database_available:
            logger.warning("Database unavailable, returning empty conversation history")
            return []
        
        try:
            await asyncio.wait_for(self._ensure_tables(), timeout=10.0)
            
            async with asyncio.timeout(30.0):  # 30 second timeout for query
                async with self._session_factory() as sess:
                    if limit is None:
                        stmt = (
                            select(self._messages.c.message_data)
                            .where(self._messages.c.session_id == self.session_id)
                            .order_by(self._messages.c.created_at.asc())
                        )
                    else:
                        stmt = (
                            select(self._messages.c.message_data)
                            .where(self._messages.c.session_id == self.session_id)
                            .order_by(self._messages.c.created_at.desc())
                            .limit(limit)
                        )

                    result = await sess.execute(stmt)
                    rows: List[str] = [row[0] for row in result.all()]

                    if limit is not None:
                        rows.reverse()

                    items: List[TResponseInputItem] = []
                    for raw in rows:
                        try:
                            items.append(json.loads(raw))
                        except json.JSONDecodeError:
                            continue
                    return items
                    
        except asyncio.TimeoutError:
            logger.error(f"Database operation timed out while retrieving items for session {self.session_id}")
            self._database_available = False
            return []
        except Exception as e:
            logger.error(f"Database error while retrieving items for session {self.session_id}: {e}")
            self._database_available = False
            return []

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        """Store new items for this session."""
        if not self._database_available:
            logger.warning("Database unavailable, conversation will not be persisted")
            return
        
        if not items:
            return

        try:
            await asyncio.wait_for(self._ensure_tables(), timeout=10.0)
            
            # Get account_id and IDs from session context (optional)
            account_id = self.session_context.get("account_id")
            team_id_int = self.session_context.get("team_id")  # Integer ID
            agent_id_int = self.session_context.get("agent_id")  # Integer ID
            team_identifier = self.session_context.get("team_identifier")  # String identifier
            agent_identifier = self.session_context.get("agent_identifier")  # String identifier
            current_time = datetime.now()
            
            # Log session context for debugging
            logger.info(f"Session context for {self.session_id}: {self.session_context}")
            logger.info(f"Extracted values - account_id: {account_id}, "
                       f"team_id: {team_id_int}, agent_id: {agent_id_int}, "
                       f"team_identifier: {team_identifier}, agent_identifier: {agent_identifier}")
            
            payload = [
                {
                    "session_id": self.session_id,
                    "message_data": await self._serialize_item(item),
                    "account_id": account_id,  # Optional - can be None
                    "created_at": current_time,
                    "updated_at": current_time,
                }
                for item in items
            ]

            async with asyncio.timeout(30.0):  # 30 second timeout for transaction
                async with self._session_factory() as sess:
                    async with sess.begin():
                        # Ensure the session exists with context
                        existing = await sess.execute(
                            select(self._sessions.c.session_id).where(
                                self._sessions.c.session_id == self.session_id
                            )
                        )
                        if not existing.scalar_one_or_none():
                            # Create session with context (all fields optional)
                            session_data = {
                                "session_id": self.session_id,
                                "account_id": account_id,  # Optional - can be None
                                "team_id": team_id_int,  # Integer ID for python-api compatibility
                                "agent_id": agent_id_int,  # Integer ID for python-api compatibility
                                "team_identifier": team_identifier,  # String identifier from YAML
                                "agent_identifier": agent_identifier,  # String identifier from YAML
                                "created_at": current_time,
                                "updated_at": current_time,
                            }
                            logger.info(f"Creating new session with data: {session_data}")
                            
                            try:
                                await sess.execute(insert(self._sessions).values(session_data))
                                logger.info(f"Successfully created session {self.session_id}")
                            except Exception as e:
                                logger.error(f"Failed to create session {self.session_id}: {e}")
                                logger.error(f"Session data that failed: {session_data}")
                                raise

                        # Insert messages in bulk
                        await sess.execute(insert(self._messages), payload)

                        # Update session timestamp
                        await sess.execute(
                            update(self._sessions)
                            .where(self._sessions.c.session_id == self.session_id)
                            .values(updated_at=current_time)
                        )
                        
        except asyncio.TimeoutError:
            logger.error(f"Database operation timed out while adding items for session {self.session_id}")
            self._database_available = False
            raise
        except Exception as e:
            logger.error(f"Database error while adding items for session {self.session_id}: {e}")
            self._database_available = False
            raise

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item from this session."""
        if not self._database_available:
            logger.warning("Database unavailable, cannot pop item")
            return None
        
        try:
            await asyncio.wait_for(self._ensure_tables(), timeout=10.0)
            
            async with asyncio.timeout(30.0):  # 30 second timeout for transaction
                async with self._session_factory() as sess:
                    async with sess.begin():
                        # Get the most recent message ID
                        subq = (
                            select(self._messages.c.id)
                            .where(self._messages.c.session_id == self.session_id)
                            .order_by(self._messages.c.created_at.desc())
                            .limit(1)
                        )
                        res = await sess.execute(subq)
                        row_id = res.scalar_one_or_none()
                        if row_id is None:
                            return None
                            
                        # Fetch data before deleting
                        res_data = await sess.execute(
                            select(self._messages.c.message_data).where(self._messages.c.id == row_id)
                        )
                        row = res_data.scalar_one_or_none()
                        await sess.execute(delete(self._messages).where(self._messages.c.id == row_id))

                        if row is None:
                            return None
                        try:
                            return json.loads(row)
                        except json.JSONDecodeError:
                            return None
                            
        except asyncio.TimeoutError:
            logger.error(f"Database operation timed out while popping item for session {self.session_id}")
            self._database_available = False
            return None
        except Exception as e:
            logger.error(f"Database error while popping item for session {self.session_id}: {e}")
            self._database_available = False
            return None

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        if not self._database_available:
            logger.warning("Database unavailable, cannot clear session")
            return
        
        try:
            await asyncio.wait_for(self._ensure_tables(), timeout=10.0)
            
            async with asyncio.timeout(30.0):  # 30 second timeout for transaction
                async with self._session_factory() as sess:
                    async with sess.begin():
                        await sess.execute(
                            delete(self._messages).where(self._messages.c.session_id == self.session_id)
                        )
                        await sess.execute(
                            delete(self._sessions).where(self._sessions.c.session_id == self.session_id)
                        )
                        
        except asyncio.TimeoutError:
            logger.error(f"Database operation timed out while clearing session {self.session_id}")
            self._database_available = False
            raise
        except Exception as e:
            logger.error(f"Database error while clearing session {self.session_id}: {e}")
            self._database_available = False
            raise
    
    async def get_sessions_by_team_or_agent(self, 
                                          team_identifier: Optional[str] = None,
                                          agent_identifier: Optional[str] = None,
                                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve sessions by team identifier and/or agent identifier.
        
        Args:
            team_identifier: Team identifier to filter by (optional)
            agent_identifier: Agent identifier to filter by (optional)
            limit: Maximum number of sessions to retrieve
            
        Returns:
            List of session data dictionaries with messages
        """
        if not self._database_available:
            logger.warning("Database unavailable, returning empty sessions list")
            return []
        
        if not team_identifier and not agent_identifier:
            logger.warning("At least one of team_identifier or agent_identifier must be provided")
            return []
        
        try:
            await asyncio.wait_for(self._ensure_tables(), timeout=10.0)
            
            async with asyncio.timeout(30.0):  # 30 second timeout for query
                async with self._session_factory() as sess:
                    from sqlalchemy import select, and_, or_
                    print(agent_identifier, team_identifier, limit)
                    # Build query conditions
                    conditions = []
                    if team_identifier:
                        conditions.append(self._sessions.c.team_identifier == team_identifier)
                    if agent_identifier:
                        conditions.append(or_(
                            self._sessions.c.agent_identifier == agent_identifier,
                            self._sessions.c.agent_identifier.like(f'%{agent_identifier}%')
                        ))
                    
                    # Query sessions
                    session_query = select(
                        self._sessions.c.session_id,
                        self._sessions.c.team_identifier,
                        self._sessions.c.agent_identifier,
                        self._sessions.c.created_at,
                        self._sessions.c.updated_at
                    ).where(and_(*conditions)).order_by(self._sessions.c.created_at.desc())
                    
                    if limit:
                        session_query = session_query.limit(limit)
                    
                    result = await sess.execute(session_query)
                    session_rows = result.fetchall()
                    
                    sessions = []
                    for row in session_rows:
                        session_id = row[0]
                        
                        # Get messages for this session
                        messages_query = select(
                            self._messages.c.message_data,
                            self._messages.c.created_at
                        ).where(
                            self._messages.c.session_id == session_id
                        ).order_by(self._messages.c.created_at.asc())
                        
                        messages_result = await sess.execute(messages_query)
                        message_rows = messages_result.fetchall()
                        
                        messages = []
                        for msg_row in message_rows:
                            try:
                                message_data = json.loads(msg_row[0])
                                messages.append({
                                    "data": message_data,
                                    "timestamp": msg_row[1].isoformat() if msg_row[1] else None
                                })
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse message data for session {session_id}")
                                continue
                        
                        session_data = {
                            "session_id": session_id,
                            "team_identifier": row[1],
                            "agent_identifier": row[2],
                            "created_at": row[3].isoformat() if row[3] else None,
                            "updated_at": row[4].isoformat() if row[4] else None,
                            "messages": messages,
                            "metadata": {
                                "team": team_identifier,
                                "agent": agent_identifier,
                                "source": "database"
                            }
                        }
                        
                        sessions.append(session_data)
                    
                    logger.info(f"Found {len(sessions)} sessions for team='{team_identifier}', agent='{agent_identifier}'")
                    return sessions
                    
        except asyncio.TimeoutError:
            logger.error(f"Database operation timed out while retrieving sessions")
            self._database_available = False
            return []
        except Exception as e:
            logger.error(f"Database error while retrieving sessions: {e}")
            self._database_available = False
            return []