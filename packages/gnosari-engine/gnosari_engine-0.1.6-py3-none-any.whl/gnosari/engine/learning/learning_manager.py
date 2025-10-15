"""Learning manager for coordinating agent learning system."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .learning_queue import LearningQueueManager, LearningEventPublisher, get_learning_queue_manager
from .learning_consumer import LearningConsumer
from ..config.configuration_manager import ConfigurationManager

logger = logging.getLogger(__name__)


class LearningManager:
    """Coordinates the agent learning system."""
    
    def __init__(self):
        self.queue_manager: Optional[LearningQueueManager] = None
        self.publisher: Optional[LearningEventPublisher] = None
        self.consumer: Optional[LearningConsumer] = None
        self.config_manager = ConfigurationManager()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the learning system."""
        if self.initialized:
            return
        
        try:
            # Initialize queue manager
            self.queue_manager = get_learning_queue_manager()
            await self.queue_manager.start()
            
            # Initialize publisher
            self.publisher = LearningEventPublisher(self.queue_manager)
            
            # Initialize consumer
            self.consumer = LearningConsumer(self.queue_manager)
            await self.consumer.start()
            
            self.initialized = True
            logger.info("Learning manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize learning manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the learning system."""
        if not self.initialized:
            return
        
        try:
            if self.consumer:
                await self.consumer.stop()
            
            if self.queue_manager:
                await self.queue_manager.stop()
            
            self.initialized = False
            logger.info("Learning manager shutdown successfully")
            
        except Exception as e:
            logger.error(f"Error during learning manager shutdown: {e}")
    
    async def add_learning(self, agent_id: str, team_path: str, learning_data: Dict[str, Any]) -> bool:
        """Add a learning for an agent."""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Publish learning request event
            await self.publisher.publish_agent_learning_request(
                agent_id=agent_id,
                team_path=team_path,
                learning_data=learning_data,
                metadata={'source': 'learning_manager'}
            )
            
            logger.info(f"Published learning request for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add learning for agent {agent_id}: {e}")
            return False
    
    def register_listening_agent(self, agent_id: str, team_path: str, listen_events: List[str]):
        """Register an agent to listen for learning events."""
        if not self.initialized:
            raise RuntimeError("Learning manager not initialized")
        
        self.consumer.register_listening_agent(agent_id, team_path, listen_events)
    
    def unregister_listening_agent(self, agent_id: str):
        """Unregister an agent from listening for events."""
        if not self.initialized:
            return
        
        self.consumer.unregister_listening_agent(agent_id)
    
    async def get_agent_learnings(self, team_path: str, agent_id: str) -> List[Dict[str, Any]]:
        """Get all learnings for an agent."""
        try:
            # Load team configuration
            team_path_obj = Path(team_path)
            
            if (team_path_obj / "main.yaml").exists():
                # Modular configuration
                modular_config = await self.config_manager.load_team_from_directory(team_path_obj)
                if agent_id in modular_config.agents:
                    agent_config = modular_config.agents[agent_id]
                    return getattr(agent_config, 'learning', [])
            else:
                # Monolithic configuration - load directly
                import yaml
                with open(team_path_obj, 'r', encoding='utf-8') as f:
                    team_config = yaml.safe_load(f)
                
                for agent in team_config.get('agents', []):
                    if agent.get('name') == agent_id:
                        return agent.get('learning', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get learnings for agent {agent_id}: {e}")
            return []
    
    async def update_learning_usage(self, agent_id: str, team_path: str, learning_index: int):
        """Update usage count for a specific learning."""
        try:
            learnings = await self.get_agent_learnings(team_path, agent_id)
            
            if 0 <= learning_index < len(learnings):
                learning = learnings[learning_index]
                learning['usage_count'] = learning.get('usage_count', 0) + 1
                learning['updated_at'] = datetime.now().isoformat()
                
                # Update in configuration
                # This would need to update the specific learning in the YAML file
                logger.debug(f"Updated usage count for learning {learning_index} of agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to update learning usage for agent {agent_id}: {e}")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        if not self.initialized:
            return {}
        
        stats = {
            'queue_size': self.queue_manager.event_queue.qsize() if self.queue_manager else 0,
            'listening_agents': len(self.consumer.get_listening_agents()) if self.consumer else 0,
            'initialized': self.initialized
        }
        
        return stats
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


# Global learning manager instance
_learning_manager: Optional[LearningManager] = None


def get_learning_manager() -> LearningManager:
    """Get the global learning manager instance."""
    global _learning_manager
    if _learning_manager is None:
        _learning_manager = LearningManager()
    return _learning_manager