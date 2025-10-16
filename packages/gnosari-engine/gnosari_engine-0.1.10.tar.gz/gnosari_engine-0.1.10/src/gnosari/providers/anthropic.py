"""
Anthropic provider implementation that returns OpenAI-compatible clients.
"""

import logging
from typing import List

from .base import BaseLLMProvider, ProviderConfig


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider that creates AsyncOpenAI clients configured for Claude models.
    
    Note: This assumes you're using a service that provides OpenAI-compatible APIs
    for Anthropic models, or you have the anthropic package configured to work
    with the OpenAI Agents SDK.
    """
    
    def __init__(self, config: ProviderConfig = None):
        """
        Initialize Anthropic provider.
        
        Args:
            config: Provider configuration
        """
        if config is None:
            config = ProviderConfig(
                env_var_name="ANTHROPIC_API_KEY",
                base_url="https://api.anthropic.com"  # Default Anthropic base URL
            )
        super().__init__(config)
    
    def create_client(self):
        """
        Create an AsyncOpenAI client configured for Anthropic.
        
        Note: This creates an OpenAI client that can be used with Anthropic models
        if you have an OpenAI-compatible proxy or if the OpenAI Agents SDK
        supports Anthropic models directly.
        
        Returns:
            Configured AsyncOpenAI client
        """
        try:
            from openai import AsyncOpenAI
            
            return AsyncOpenAI(
                api_key=self.get_api_key(),
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    
    def get_supported_models(self) -> List[str]:
        """
        Get Anthropic supported models.
        
        Returns:
            List of supported model names
        """
        return [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022', 
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ]