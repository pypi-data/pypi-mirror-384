"""
DeepSeek provider implementation.
"""

import logging
from typing import List

from .base import BaseLLMProvider, ProviderConfig


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek LLM provider that creates AsyncOpenAI clients.
    
    DeepSeek provides OpenAI-compatible APIs, so we can use AsyncOpenAI
    with their base URL and API key.
    """
    
    def __init__(self, config: ProviderConfig = None):
        """
        Initialize DeepSeek provider.
        
        Args:
            config: Provider configuration
        """
        if config is None:
            config = ProviderConfig(
                env_var_name="DEEPSEEK_API_KEY",
                base_url="https://api.deepseek.com"
            )
        super().__init__(config)
    
    def create_client(self):
        """
        Create an AsyncOpenAI client configured for DeepSeek.
        
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
        Get DeepSeek supported models.
        
        Returns:
            List of supported model names
        """
        return [
            'deepseek-chat',
            'deepseek-coder',
            'deepseek-reasoner'
        ]