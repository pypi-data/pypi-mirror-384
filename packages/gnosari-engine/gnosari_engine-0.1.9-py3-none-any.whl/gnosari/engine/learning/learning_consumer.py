"""Learning consumer for processing queue events and updating configurations."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .learning_queue import LearningEvent, LearningEventType, LearningQueueManager
from ..config.configuration_manager import ConfigurationManager

logger = logging.getLogger(__name__)


class LearningConsumer:
    """Consumer for processing learning events and updating agent configurations."""
    
    def __init__(self, queue_manager: LearningQueueManager):
        self.queue_manager = queue_manager
        self.config_manager = ConfigurationManager()
        self.listening_agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> config
        self.running = False
        
    async def start(self):
        """Start the learning consumer."""
        if self.running:
            return
        
        self.running = True
        
        # Subscribe to learning events
        self.queue_manager.subscribe(
            LearningEventType.AGENT_LEARNING_REQUEST,
            self._handle_learning_request
        )
        
        logger.info("Learning consumer started")
    
    async def stop(self):
        """Stop the learning consumer."""
        if not self.running:
            return
        
        self.running = False
        
        # Unsubscribe from events
        self.queue_manager.unsubscribe(
            LearningEventType.AGENT_LEARNING_REQUEST,
            self._handle_learning_request
        )
        
        logger.info("Learning consumer stopped")
    
    def register_listening_agent(self, agent_id: str, team_path: str, listen_events: List[str]):
        """Register an agent to listen for specific learning events."""
        self.listening_agents[agent_id] = {
            'team_path': team_path,
            'listen_events': listen_events
        }
        logger.info(f"Registered agent {agent_id} to listen for events: {listen_events}")
    
    def unregister_listening_agent(self, agent_id: str):
        """Unregister an agent from listening for events."""
        if agent_id in self.listening_agents:
            del self.listening_agents[agent_id]
            logger.info(f"Unregistered agent {agent_id} from listening for events")
    
    async def _handle_learning_request(self, event: LearningEvent):
        """Handle agent learning request events."""
        try:
            logger.info(f"Processing learning request for agent {event.agent_id}")
            
            # Validate learning data
            if not self._validate_learning_data(event.learning_data):
                logger.error(f"Invalid learning data for agent {event.agent_id}")
                return
            
            # Add learning to agent configuration
            team_path = Path(event.team_path)
            success = await self.config_manager.add_learning_to_agent(
                team_path, 
                event.agent_id, 
                event.learning_data
            )
            
            if success:
                logger.info(f"Successfully added learning to agent {event.agent_id}")
                
                # Notify listening agents if configured
                await self._notify_listening_agents(event)
                
                # Publish learning added event
                from .learning_queue import LearningEventPublisher
                publisher = LearningEventPublisher(self.queue_manager)
                await publisher.publish_learning_added(
                    event.agent_id,
                    event.team_path,
                    event.learning_data,
                    {'processed_by': 'learning_consumer'}
                )
            else:
                logger.error(f"Failed to add learning to agent {event.agent_id}")
                
        except Exception as e:
            logger.error(f"Error handling learning request for agent {event.agent_id}: {e}")
    
    def _validate_learning_data(self, learning_data: Dict[str, Any]) -> bool:
        """Validate learning data structure."""
        required_fields = ['type', 'content']
        
        for field in required_fields:
            if field not in learning_data:
                logger.error(f"Missing required field in learning data: {field}")
                return False
            
            if not isinstance(learning_data[field], str) or not learning_data[field].strip():
                logger.error(f"Invalid value for field {field} in learning data")
                return False
        
        # Validate content length
        content = learning_data['content']
        if len(content.strip()) < 10:
            logger.error("Learning content must be at least 10 characters")
            return False
        
        if len(content) > 2000:
            logger.error("Learning content must be less than 2000 characters")
            return False
        
        # Validate priority if present
        if 'priority' in learning_data:
            valid_priorities = ['critical', 'high', 'medium', 'low', 'contextual']
            if learning_data['priority'].lower() not in valid_priorities:
                logger.error(f"Invalid priority: {learning_data['priority']}")
                return False
        
        return True
    
    async def _notify_listening_agents(self, event: LearningEvent):
        """Notify agents that are listening for learning events."""
        event_type = event.event_type.value
        
        for agent_id, config in self.listening_agents.items():
            listen_events = config.get('listen_events', [])
            
            if event_type in listen_events or 'all' in listen_events:
                logger.debug(f"Notifying listening agent {agent_id} of event {event_type}")
                
                # Here you could implement specific notification logic
                # For example, updating the agent's context or sending a message
                # This is where future agent-to-agent learning sharing could be implemented
    
    def get_listening_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered listening agents."""
        return self.listening_agents.copy()
    
    async def process_pending_learning_requests(self, team_path: str, agent_id: str):
        """Process any pending learning requests for a specific agent."""
        # This method could be used to replay events or handle missed events
        # when an agent comes online
        logger.debug(f"Processing pending learning requests for agent {agent_id}")
        
        # Implementation could include:
        # 1. Check for any queued events for this agent
        # 2. Load recent learning events from persistence
        # 3. Apply any missed learnings
        pass


class LearningEventFilter:
    """Filter for learning events based on agent configuration."""
    
    def __init__(self, agent_id: str, listen_events: List[str]):
        self.agent_id = agent_id
        self.listen_events = set(listen_events)
    
    def should_process_event(self, event: LearningEvent) -> bool:
        """Determine if this agent should process the given event."""
        # Process if listening for all events
        if 'all' in self.listen_events:
            return True
        
        # Process if listening for this specific event type
        if event.event_type.value in self.listen_events:
            return True
        
        # Process if the event is specifically for this agent
        if event.agent_id == self.agent_id:
            return True
        
        return False
    
    def filter_learning_data(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter learning data based on agent preferences."""
        # This could implement filtering logic based on:
        # - Learning type preferences
        # - Priority thresholds
        # - Context matching
        # - Tag filtering
        
        return learning_data  # For now, return as-is