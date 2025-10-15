"""Agent-specific type definitions."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .core import ProductResult, Message, ConversationContext


class AgentResponse(BaseModel):
    """Agent response."""
    
    model_config = ConfigDict(extra='forbid')
    
    message: str = Field(..., description="Response message")
    products: Optional[List[ProductResult]] = Field(default=None, description="Product results")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")
    success: bool = Field(default=True, description="Whether the response was successful")


class ToolResult(BaseModel):
    """Tool execution result."""
    
    model_config = ConfigDict(extra='forbid')
    
    success: bool = Field(..., description="Whether tool execution was successful")
    result: Optional[Any] = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class IntentDetectionResult(BaseModel):
    """Intent detection result."""
    
    model_config = ConfigDict(extra='forbid')
    
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    entities: Optional[Dict[str, Any]] = Field(default=None, description="Extracted entities")
    synonyms_matched: Optional[List[str]] = Field(default=None, description="Matched synonyms")


class SearchRequest(BaseModel):
    """Product search request."""
    
    model_config = ConfigDict(extra='forbid')
    
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    limit: int = Field(default=20, ge=1, le=100, description="Result limit")
    offset: int = Field(default=0, ge=0, description="Result offset")
    session_id: Optional[str] = Field(default=None, description="Session ID")


class SearchResponse(BaseModel):
    """Product search response."""
    
    model_config = ConfigDict(extra='forbid')
    
    products: List[ProductResult] = Field(default_factory=list, description="Search results")
    total_count: int = Field(default=0, description="Total number of results")
    query: str = Field(..., description="Original query")
    filters_applied: Optional[Dict[str, Any]] = Field(default=None, description="Applied filters")
    search_time_ms: Optional[float] = Field(default=None, description="Search execution time")


class AgentState(BaseModel):
    """Agent state for conversation management."""
    
    model_config = ConfigDict(extra='forbid')
    
    conversation_context: ConversationContext = Field(..., description="Conversation context")
    current_intent: Optional[str] = Field(default=None, description="Current detected intent")
    last_tool_used: Optional[str] = Field(default=None, description="Last tool used")
    last_query: Optional[str] = Field(default=None, description="Last user query")
    conversation_turns: int = Field(default=0, description="Number of conversation turns")
    is_discovery_mode: bool = Field(default=False, description="Whether in discovery mode")
    user_satisfied: bool = Field(default=False, description="Whether user is satisfied")
    retry_count: int = Field(default=0, description="Number of retries for current intent")
