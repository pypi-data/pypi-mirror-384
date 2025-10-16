"""Gnosari API-based learning storage implementation."""

import os
import requests
from typing import Dict, Any
from datetime import datetime

from .base import BaseLearningStorage
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GnosariAPILearningStorage(BaseLearningStorage):
    """Learning storage implementation using Gnosari API."""
    
    def __init__(self):
        """Initialize the Gnosari API storage."""
        self.api_url = os.getenv("GNOSARI_API_URL", "https://api.gnosari.com")
        self.api_key = os.getenv("GNOSARI_API_KEY")
        
        if not self.api_key:
            logger.warning("GNOSARI_API_KEY not found in environment variables")
    
    def store_learning(self, session: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Store learning data using Gnosari API.
        
        Args:
            session: Session information containing team and agent identifiers
            data: Learning data to store
            
        Returns:
            bool: True if learning was successfully stored, False otherwise
        """
        if not self.api_key:
            logger.error("Cannot store learning: GNOSARI_API_KEY not configured")
            return False
        
        try:
            # Extract learning data
            learning_entry = self._create_learning_payload(session, data)
            
            # Make API request
            headers = {
                "Content-Type": "application/json",
                "X-Auth-Token": self.api_key
            }
            
            url = f"{self.api_url.rstrip('/')}/api/v1/learning/"
            
            logger.info(f"Storing learning via Gnosari API: {url}")
            response = requests.post(url, json=learning_entry, headers=headers, timeout=30)
            
            if response.status_code in (200, 201):
                logger.info("Successfully stored learning via Gnosari API")
                return True
            else:
                logger.error(f"Failed to store learning via Gnosari API. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error storing learning via Gnosari API: {e}")
            return False
        except Exception as e:
            logger.error(f"Error storing learning via Gnosari API: {e}")
            return False
    
    def _create_learning_payload(self, session: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Create the payload for the Gnosari API learning endpoint.
        
        Args:
            session: Session information
            data: Learning data from the event
            
        Returns:
            Dict[str, Any]: API payload
        """
        # Extract learning data from nested structure
        actual_data = data.get("data", {})
        learning_data = actual_data.get("learning", {})
        
        # Get learning content and metadata
        content = learning_data.get("content") or data.get("content", "Learning from agent interaction")
        learning_type = learning_data.get("type") or data.get("type", "agent_interaction")
        priority = learning_data.get("priority") or data.get("priority", "medium")
        context = learning_data.get("context") or data.get("context", "Agent interaction")
        tags = learning_data.get("tags") or data.get("tags", ["agent_learning", "interaction"])
        
        # Convert numeric priority to string if needed
        if isinstance(priority, (int, float)):
            priority_map = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "contextual"}
            priority = priority_map.get(int(priority), "medium")
        
        # Get agent_id from session (convert to integer if possible, fallback to 1)
        agent_id = session.get("agent_id") or session.get("agent_identifier")
        
        # Convert to integer for API compatibility
        if isinstance(agent_id, str):
            # For string identifiers, use a simple hash-based mapping or default to 1
            agent_id = 1  # Default fallback for string identifiers
        elif agent_id is None:
            agent_id = 1
        
        payload = {
            "agent_id": agent_id,
            "content": content,
            "learning_type": learning_type,
            "priority": priority,
            "context": context,
            "tags": tags
        }
        
        logger.debug(f"Created Gnosari API payload: {payload}")
        return payload