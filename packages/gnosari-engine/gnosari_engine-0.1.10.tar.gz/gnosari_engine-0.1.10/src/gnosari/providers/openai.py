"""
OpenAI provider implementation.
"""

import logging
from typing import List

from .base import BaseLLMProvider, ProviderConfig


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider that creates AsyncOpenAI clients.
    """
    
    def __init__(self, config: ProviderConfig = None):
        """
        Initialize OpenAI provider.
        
        Args:
            config: Provider configuration
        """
        if config is None:
            config = ProviderConfig(
                env_var_name="OPENAI_API_KEY"
            )
        super().__init__(config)
    
    def create_client(self):
        """
        Create an AsyncOpenAI client for OpenAI.
        
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
        Get OpenAI supported models.
        
        Returns:
            List of supported model names
        """
        return [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo',
            'o1-preview',
            'o1-mini',
            'gpt-5'  # Added for future compatibility
        ]