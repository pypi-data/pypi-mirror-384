"""
API session implementation for remote backend
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from agents.memory.session import SessionABC
from agents.items import TResponseInputItem
from ..schemas import SessionContext

logger = logging.getLogger(__name__)


class ApiSession(SessionABC):
    """API session implementation for remote backend."""

    def __init__(self, 
                 session_id: str, 
                 session_context: Optional[SessionContext] = None,
                 api_base_url: Optional[str] = None,
                 api_key: Optional[str] = None):
        """Initialize API session.
        
        Args:
            session_id: Unique identifier for the conversation
            session_context: SessionContext object containing account_id, team_id, agent_id
            api_base_url: Base URL for the API
            api_key: API authentication key
        """
        self.session_id = session_id
        self._session_context_obj = session_context
        
        # Convert SessionContext to dictionary for internal use
        if session_context is not None:
            self.session_context = session_context.model_dump(exclude_none=True)
        else:
            self.session_context = {}
        
        # Validate required parameters
        if not api_base_url or not api_key:
            raise ValueError("api_base_url and api_key are required for ApiSession")
        
        if not session_context or not self.session_context.get("account_id"):
            raise ValueError("account_id in session_context is required for ApiSession")
        
        try:
            import aiohttp
            self._api_base_url = api_base_url.rstrip('/')
            self._api_key = api_key
            logger.info(f"Initialized ApiSession for session_id: {session_id}, API: {api_base_url}")
        except ImportError:
            raise ImportError("aiohttp is required for ApiSession")
    
    async def cleanup(self):
        """Clean up API session resources."""
        # API sessions don't need explicit cleanup
        logger.debug(f"Cleaned up API session {self.session_id}")
    
    def _get_http_session(self):
        """Get HTTP session for API requests."""
        import aiohttp
        return aiohttp.ClientSession()

    async def _get_auth_headers(self) -> dict:
        """Get authentication headers for API requests."""
        return {
            "X-Auth-Token": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _ensure_session_exists(self) -> None:
        """Ensure the session exists in the API backend."""
        try:
            headers = await self._get_auth_headers()
            
            async with self._get_http_session() as session:
                async with session.get(
                    f"{self._api_base_url}/api/v1/sessions/{self.session_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Session {self.session_id} already exists")
                        return
                    elif response.status != 404:
                        response.raise_for_status()
            
            # Create session if it doesn't exist
            session_data = {
                "session_id": self.session_id,
                "team_identifier": self.session_context.get("team_id"),
                "agent_identifier": self.session_context.get("agent_id"),
                "messages": []
            }
            
            async with self._get_http_session() as session:
                async with session.post(
                    f"{self._api_base_url}/api/v1/sessions",
                    headers=headers,
                    json=session_data
                ) as response:
                    if response.status == 201:
                        logger.info(f"Created session {self.session_id} in API backend")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create session: {response.status} - {error_text}")
                        response.raise_for_status()
                        
        except Exception as e:
            logger.error(f"Error ensuring session exists: {e}")
            raise

    async def get_items(self, limit: int | None = None) -> List[TResponseInputItem]:
        """Retrieve conversation history via API."""
        try:
            async with asyncio.timeout(60.0):  # 60 second timeout for API operations
                await self._ensure_session_exists()
                headers = await self._get_auth_headers()
                
                url = f"{self._api_base_url}/api/v1/sessions/{self.session_id}/messages"
                if limit:
                    url += f"?limit={limit}"
                
                async with self._get_http_session() as session:
                    async with session.get(
                        url,
                        headers=headers,
                        timeout=30  # 30 second HTTP timeout
                    ) as response:
                        if response.status == 200:
                            messages = await response.json()
                            items = []
                            for message in messages:
                                try:
                                    item = json.loads(message["message_data"])
                                    items.append(item)
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to parse message data: {message['message_data']}")
                                    continue
                            
                            logger.debug(f"Retrieved {len(items)} items for session {self.session_id}")
                            return items
                        else:
                            error_text = await response.text()
                            logger.error(f"Failed to get messages: {response.status} - {error_text}")
                            return []
                            
        except asyncio.TimeoutError:
            logger.error(f"API operation timed out while retrieving items for session {self.session_id}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving items via API: {e}")
            return []

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        """Store new items via API."""
        if not items:
            return
            
        try:
            async with asyncio.timeout(60.0):  # 60 second timeout for API operations
                await self._ensure_session_exists()
                headers = await self._get_auth_headers()
                
                messages = []
                for item in items:
                    # Use a more robust serialization approach to preserve reasoning items
                    try:
                        # First try to use the item's built-in serialization if available
                        if hasattr(item, 'model_dump') or hasattr(item, 'dict'):
                            if hasattr(item, 'model_dump'):
                                message_data = json.dumps(item.model_dump(), separators=(",", ":"))
                            else:
                                message_data = json.dumps(item.dict(), separators=(",", ":"))
                        else:
                            # Fall back to standard JSON serialization
                            message_data = json.dumps(item, separators=(",", ":"))
                    except (TypeError, AttributeError) as e:
                        logger.warning(f"Failed to serialize item properly: {e}, using string representation")
                        message_data = json.dumps(str(item), separators=(",", ":"))
                    
                    messages.append({"message_data": message_data})
                
                async with self._get_http_session() as session:
                    async with session.post(
                        f"{self._api_base_url}/api/v1/sessions/{self.session_id}/messages",
                        headers=headers,
                        json=messages,
                        timeout=30  # 30 second HTTP timeout
                    ) as response:
                        if response.status == 200:
                            logger.debug(f"Added {len(items)} items to session {self.session_id}")
                        else:
                            error_text = await response.text()
                            logger.error(f"Failed to add messages: {response.status} - {error_text}")
                            response.raise_for_status()
                            
        except asyncio.TimeoutError:
            logger.error(f"API operation timed out while adding items for session {self.session_id}")
            raise
        except Exception as e:
            logger.error(f"Error adding items via API: {e}")
            raise

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item via API."""
        try:
            await self._ensure_session_exists()
            headers = await self._get_auth_headers()
            
            async with self._get_http_session() as session:
                async with session.delete(
                    f"{self._api_base_url}/api/v1/sessions/{self.session_id}/messages/latest",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        message = await response.json()
                        if message:
                            try:
                                item = json.loads(message["message_data"])
                                logger.debug(f"Popped item from session {self.session_id}")
                                return item
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse popped message data: {message['message_data']}")
                                return None
                        else:
                            return None
                    else:
                        logger.error(f"Failed to pop message: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error popping item via API: {e}")
            return None

    async def clear_session(self) -> None:
        """Clear all items via API."""
        try:
            await self._ensure_session_exists()
            headers = await self._get_auth_headers()
            
            async with self._get_http_session() as session:
                async with session.delete(
                    f"{self._api_base_url}/api/v1/sessions/{self.session_id}/messages",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Cleared all messages from session {self.session_id}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to clear messages: {response.status} - {error_text}")
                        response.raise_for_status()
                        
        except Exception as e:
            logger.error(f"Error clearing session via API: {e}")
            raise