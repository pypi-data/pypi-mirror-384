"""
LLM provider abstractions for Gnosari AI Teams.

This package provides simplified providers that create properly configured
AsyncOpenAI clients for use with the OpenAI Agents SDK. Each provider
handles the specific API key environment variables and base URLs needed
for different LLM services.
"""

from .base import BaseLLMProvider, ProviderConfig, ProviderRegistry, provider_registry
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider  
from .deepseek import DeepSeekProvider
from .setup import (
    setup_provider_for_model, 
    setup_provider_by_name, 
    list_available_models,
    get_provider_for_model
)

# Auto-register default providers
_openai_provider = OpenAIProvider()
_anthropic_provider = AnthropicProvider()
_deepseek_provider = DeepSeekProvider()

provider_registry.register(_openai_provider)
provider_registry.register(_anthropic_provider)
provider_registry.register(_deepseek_provider)

__all__ = [
    'BaseLLMProvider',
    'ProviderConfig',
    'ProviderRegistry',
    'provider_registry',
    'OpenAIProvider',
    'AnthropicProvider',
    'DeepSeekProvider',
    'setup_provider_for_model',
    'setup_provider_by_name',
    'list_available_models',
    'get_provider_for_model'
]