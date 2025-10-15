"""Type definitions for the catalog agent."""

from .core import (
    AgentConfig,
    ProductResult,
    Message,
    MessageRole,
    ConversationContext,
    FilterCriteria,
    CatalogAgentError,
    ValidationError,
    APIError,
    ConfigurationError,
)
from .agent import (
    AgentResponse,
    ToolResult,
    IntentDetectionResult,
    SearchRequest,
    SearchResponse,
    AgentState,
)

__all__ = [
    # Core types
    "AgentConfig",
    "ProductResult",
    "Message",
    "MessageRole",
    "ConversationContext",
    "FilterCriteria",
    # Error types
    "CatalogAgentError",
    "ValidationError",
    "APIError",
    "ConfigurationError",
    # Agent types
    "AgentResponse",
    "ToolResult",
    "IntentDetectionResult",
    "SearchRequest",
    "SearchResponse",
    "AgentState",
]
