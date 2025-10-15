"""Core type definitions for the catalog agent."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class AgentConfig(BaseModel):
    """Configuration for the catalog agent."""
    
    model_config = ConfigDict(extra='forbid')
    
    openai_api_key: str = Field(..., min_length=1, description="OpenAI API key")
    supabase_functions_url: str = Field(..., description="Supabase Functions URL")
    gpt_actions_api_key: str = Field(..., min_length=1, description="GPT Actions API key")
    config_path: str = Field(default="./config", description="Path to config files")
    shop_domain: str = Field(default="shop.styledgenie.com", description="Shop domain")
    model: str = Field(default="gpt-4", description="OpenAI model to use")
    temperature: float = Field(default=0.1, ge=0, le=2, description="Model temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens to generate")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    debug: bool = Field(default=False, description="Enable debug mode")


class ProductResult(BaseModel):
    """Product search result."""
    
    model_config = ConfigDict(extra='forbid')
    
    handle: str = Field(..., description="Product handle")
    title: str = Field(..., description="Product title")
    url: str = Field(..., description="Product URL")
    image_url: Optional[str] = Field(default=None, description="Product image URL")
    score: Optional[float] = Field(default=None, ge=0, le=1, description="Search relevance score")
    boosted: Optional[bool] = Field(default=None, description="Whether product is boosted")


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Agent message."""
    
    model_config = ConfigDict(extra='forbid')
    
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")
    session_id: Optional[str] = Field(default=None, description="Session ID")


class ConversationContext(BaseModel):
    """Conversation context."""
    
    model_config = ConfigDict(extra='forbid')
    
    session_id: str = Field(..., description="Session ID")
    messages: List[Message] = Field(default_factory=list, description="Message history")
    user_preferences: Optional[Dict[str, List[str]]] = Field(
        default=None, 
        description="User preferences (sizes, colors, brands, etc.)"
    )
    catalog_discovered: bool = Field(default=False, description="Whether catalog was discovered")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    intent_failures: int = Field(default=0, description="Number of intent detection failures")
    last_query: Optional[str] = Field(default=None, description="Last user query")
    last_intent_summary: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Last intent detection summary"
    )
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")
    created_at: Optional[datetime] = Field(default=None, description="Session creation time")


class FilterCriteria(BaseModel):
    """Product filter criteria."""
    
    model_config = ConfigDict(extra='forbid')
    
    query: Optional[str] = Field(default=None, description="Search query")
    category: Optional[str] = Field(default=None, description="Product category")
    brand: Optional[str] = Field(default=None, description="Brand filter")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price")
    size: Optional[str] = Field(default=None, description="Size filter")
    color: Optional[str] = Field(default=None, description="Color filter")
    in_stock: Optional[bool] = Field(default=None, description="In stock filter")
    limit: Optional[int] = Field(default=20, ge=1, le=100, description="Result limit")
    offset: Optional[int] = Field(default=0, ge=0, description="Result offset")


# ============================================
# Error Types
# ============================================

class CatalogAgentError(Exception):
    """Base exception for catalog agent errors."""
    
    def __init__(
        self, 
        message: str, 
        code: str, 
        status_code: Optional[int] = None, 
        details: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ValidationError(CatalogAgentError):
    """Validation error."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class APIError(CatalogAgentError):
    """API error."""
    
    def __init__(self, message: str, status_code: int, details: Optional[Any] = None):
        super().__init__(message, "API_ERROR", status_code, details)


class ConfigurationError(CatalogAgentError):
    """Configuration error."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "CONFIGURATION_ERROR", 500, details)
