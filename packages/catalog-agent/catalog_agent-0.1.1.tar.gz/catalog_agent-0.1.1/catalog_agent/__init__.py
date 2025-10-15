"""Catalog Agent - AI-powered product discovery and recommendations."""

from .agent.catalog_agent import CatalogAgent
from .intent.intent_service import IntentService
from .types.core import Message, ProductResult, FilterCriteria, AgentConfig
from .types.agent import AgentResponse

__version__ = "0.1.0"
__all__ = [
    "CatalogAgent",
    "IntentService",
    "Message",
    "ProductResult",
    "FilterCriteria",
    "AgentConfig",
    "AgentResponse",
]
