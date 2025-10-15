"""Core components of the Campfires framework."""

from .torch import Torch
from .camper import Camper
from .campfire import Campfire
from .state_manager import StateManager
from .openrouter import (
    OpenRouterClient, 
    OpenRouterConfig, 
    ChatMessage, 
    ChatRequest, 
    ChatResponse,
    LLMCamperMixin,
    quick_completion,
    quick_chat
)

__all__ = [
    "Torch", 
    "Camper", 
    "Campfire", 
    "StateManager",
    "OpenRouterClient",
    "OpenRouterConfig",
    "ChatMessage",
    "ChatRequest", 
    "ChatResponse",
    "LLMCamperMixin",
    "quick_completion",
    "quick_chat"
]