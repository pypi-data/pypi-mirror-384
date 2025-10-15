"""Handoff configuration functionality for agents."""

import logging
from typing import Dict, Any, List
from agents import handoff
from pydantic import BaseModel


class HandoffEscalationData(BaseModel):
    """Data model for handoff escalation events."""
    reason: str
    from_agent: str
    to_agent: str
    context: str = None
    conversation_history: str = None


async def on_handoff_escalation(ctx, input_data: HandoffEscalationData):
    """Callback function for handoff escalation events."""
    logger = logging.getLogger(__name__)
    logger.info(f"🤝 HANDOFF ESCALATION: {input_data.from_agent} → {input_data.to_agent}")
    logger.info(f"📋 Reason: {input_data.reason}")
    if input_data.context:
        logger.info(f"📝 Context: {input_data.context}")
        input_data.conversation_history = input_data.context


class HandoffConfigurator:
    """Configures handoffs between agents."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def configure_handoffs(self, all_agents: Dict[str, Dict[str, Any]]) -> None:
        """
        Configure handoffs for all agents based on can_transfer_to configuration.
        
        Args:
            all_agents: Dictionary mapping agent names to agent info (agent, config, is_orchestrator)
        """
        for agent_name, agent_info in all_agents.items():
            self._configure_agent_handoffs(agent_name, agent_info, all_agents)
    
    def _configure_agent_handoffs(
        self, 
        agent_name: str, 
        agent_info: Dict[str, Any], 
        all_agents: Dict[str, Dict[str, Any]]
    ) -> None:
        """Configure handoffs for a single agent."""
        agent = agent_info['agent']
        agent_config = agent_info['config']
        can_transfer_to = agent_config.get('can_transfer_to', [])
        
        if not can_transfer_to:
            return
        
        handoffs_list = []
        handoff_targets = []
        
        # Handle both old format (list of strings) and new format (list of objects)
        for transfer_config in can_transfer_to:
            target_agent_name, transfer_instructions = self._parse_transfer_config(transfer_config, agent_name)
            
            if not target_agent_name:
                continue
            
            if target_agent_name in all_agents:
                handoff_obj = self._create_handoff(target_agent_name, all_agents, transfer_instructions)
                if handoff_obj:
                    handoffs_list.append(handoff_obj)
                    handoff_targets.append(target_agent_name)
                    
                    if transfer_instructions:
                        self.logger.info(f"🔗 Set up handoff from '{agent_name}' to '{target_agent_name}' with instructions: {transfer_instructions}")
                    else:
                        self.logger.info(f"🔗 Set up handoff from '{agent_name}' to '{target_agent_name}'")
            else:
                self.logger.warning(f"⚠️  Agent '{agent_name}' configured to transfer to '{target_agent_name}', but that agent doesn't exist")
        
        # Set handoffs for this agent
        agent.handoffs = handoffs_list
        
        if agent_info['is_orchestrator']:
            self.logger.info(f"🎯 Set up handoffs for orchestrator '{agent_name}': {handoff_targets}")
        else:
            self.logger.info(f"🤝 Set up handoffs for worker '{agent_name}': {handoff_targets}")
    
    def _parse_transfer_config(self, transfer_config: Any, agent_name: str) -> tuple[str, str]:
        """
        Parse transfer configuration to extract target agent name and instructions.
        
        Returns:
            Tuple of (target_agent_name, transfer_instructions)
        """
        if isinstance(transfer_config, str):
            # Old format: just agent name
            return transfer_config, None
        elif isinstance(transfer_config, dict):
            # New format: object with agent and instructions
            target_agent_name = transfer_config.get('agent')
            transfer_instructions = transfer_config.get('instructions')
            return target_agent_name, transfer_instructions
        else:
            self.logger.warning(f"Invalid can_transfer_to configuration for agent '{agent_name}': {transfer_config}")
            return None, None
    
    def _create_handoff(
        self, 
        target_agent_name: str, 
        all_agents: Dict[str, Dict[str, Any]], 
        transfer_instructions: str
    ) -> Any:
        """Create a handoff object for the target agent."""
        try:
            target_agent = all_agents[target_agent_name]['agent']
            
            # Create handoff with escalation callback
            handoff_obj = handoff(
                agent=target_agent,
                on_handoff=on_handoff_escalation,
                input_type=HandoffEscalationData
            )
            
            return handoff_obj
            
        except Exception as e:
            self.logger.error(f"Failed to create handoff to '{target_agent_name}': {e}")
            return None