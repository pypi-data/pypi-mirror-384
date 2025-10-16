"""
Base provider interface for LLM integrations with OpenAI Agents SDK.

Since the OpenAI Agents SDK handles all LLM calls, providers just need to
return properly configured AsyncOpenAI clients with the right base_url and API keys.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for LLM providers."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    env_var_name: str = "OPENAI_API_KEY"
    timeout: int = 300


class BaseLLMProvider(ABC):
    """
    Base class for LLM providers that create AsyncOpenAI clients.
    
    The OpenAI Agents SDK handles all the actual LLM calls, so providers
    just need to configure the right AsyncOpenAI client instance.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize the provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def create_client(self):
        """
        Create an AsyncOpenAI client configured for this provider.
        
        Returns:
            Configured AsyncOpenAI client instance
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of models supported by this provider.
        
        Returns:
            List of supported model names
        """
        pass
    
    def get_api_key(self) -> str:
        """
        Get the API key for this provider.
        
        Returns:
            API key from config or environment
        """
        return (
            self.config.api_key or 
            os.getenv(self.config.env_var_name) or
            ""
        )
    
    def get_provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            Provider name
        """
        return self.__class__.__name__.replace('Provider', '').lower()


class ProviderRegistry:
    """Registry for managing LLM providers."""
    
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._model_to_provider: Dict[str, str] = {}
    
    def register(self, provider: BaseLLMProvider) -> None:
        """Register an LLM provider."""
        provider_name = provider.get_provider_name()
        self._providers[provider_name] = provider
        
        # Map supported models to this provider
        for model in provider.get_supported_models():
            self._model_to_provider[model] = provider_name
    
    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """Get a provider by name."""
        return self._providers.get(name)
    
    def get_provider_for_model(self, model: str) -> Optional[BaseLLMProvider]:
        """Get the appropriate provider for a model."""
        provider_name = self._model_to_provider.get(model)
        if provider_name:
            return self._providers.get(provider_name)
        return None
    
    def create_client_for_model(self, model: str):
        """Create an AsyncOpenAI client for a specific model."""
        provider = self.get_provider_for_model(model)
        if provider:
            return provider.create_client()
        return None
    
    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
    
    def list_supported_models(self) -> Dict[str, List[str]]:
        """List all supported models by provider."""
        return {
            name: provider.get_supported_models() 
            for name, provider in self._providers.items()
        }


# Global provider registry
provider_registry = ProviderRegistry()