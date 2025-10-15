"""LangChain tools for the catalog agent."""

import json
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from .supabase_client import SupabaseClient
from ..types.core import ProductResult, APIError, ValidationError


@tool
def search_embedding(
    query: str,
    limit: int = 20,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """AI-powered semantic search for complex queries requiring understanding of style, context, and meaning.
    
    Use for queries like "comfortable summer dress for beach wedding", "casual Friday office outfit", or "elegant formal wear". Can work with filtered results or search all products.
    
    Args:
        query: Search query text
        limit: Maximum number of results (default: 20)
        offset: Number of results to skip (default: 0)
        filters: Additional filters to apply
        
    Returns:
        JSON string with search results
    """
    try:
        # This will be injected by the agent
        supabase_client = getattr(search_embedding, '_supabase_client', None)
        if not supabase_client:
            raise APIError("Supabase client not initialized", 500)
        
        products = supabase_client.search_products(
            query=query,
            limit=limit,
            offset=offset,
            filters=filters
        )
        
        result = {
            "success": True,
            "results": [product.model_dump() for product in products],
            "count": len(products),
            "query": query,
            "filters_applied": filters or {}
        }
        
        return json.dumps(result)
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "query": query
        }
        return json.dumps(error_result)


@tool
def filter_products(
    filters: Dict[str, Any],
    limit: int = 20,
    offset: int = 0
) -> str:
    """Filter products by specific criteria like brand, category, price, etc.
    
    Use this tool when the user mentions specific attributes, categories, or brands.
    Examples: "red cotton shirts for men", "Nike running shoes", "size M or L dresses".
    
    Args:
        filters: Dictionary of filter criteria
        limit: Maximum number of results (default: 20)
        offset: Number of results to skip (default: 0)
        
    Returns:
        JSON string with filtered results
    """
    try:
        supabase_client = getattr(filter_products, '_supabase_client', None)
        if not supabase_client:
            raise APIError("Supabase client not initialized", 500)
        
        products = supabase_client.filter_products(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        result = {
            "success": True,
            "results": [product.model_dump() for product in products],
            "count": len(products),
            "filters_applied": filters
        }
        
        return json.dumps(result)
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "filters": filters
        }
        return json.dumps(error_result)


@tool
def discover_products(
    user_preferences: Optional[Dict[str, Any]] = None,
    limit: int = 20
) -> str:
    """Discover products based on user preferences and behavior.
    
    Use this tool when the user wants personalized recommendations or to discover new products.
    Examples: "show me something new", "recommend products for me", "what's trending".
    
    Args:
        user_preferences: User preferences for discovery
        limit: Maximum number of results (default: 20)
        
    Returns:
        JSON string with discovered products
    """
    try:
        supabase_client = getattr(discover_products, '_supabase_client', None)
        if not supabase_client:
            raise APIError("Supabase client not initialized", 500)
        
        products = supabase_client.discover_products(
            user_preferences=user_preferences,
            limit=limit
        )
        
        result = {
            "success": True,
            "results": [product.model_dump() for product in products],
            "count": len(products),
            "user_preferences": user_preferences or {}
        }
        
        return json.dumps(result)
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "user_preferences": user_preferences
        }
        return json.dumps(error_result)


@tool
def get_product_details(handle: str) -> str:
    """Get detailed information about a specific product.
    
    Use this tool when the user asks for details about a specific product.
    Examples: "tell me about this laptop", "what are the specs of this dress".
    
    Args:
        handle: Product handle/identifier
        
    Returns:
        JSON string with product details
    """
    try:
        supabase_client = getattr(get_product_details, '_supabase_client', None)
        if not supabase_client:
            raise APIError("Supabase client not initialized", 500)
        
        product = supabase_client.get_product_by_handle(handle)
        
        if product:
            result = {
                "success": True,
                "product": product.model_dump(),
                "found": True
            }
        else:
            result = {
                "success": True,
                "product": None,
                "found": False,
                "message": f"Product with handle '{handle}' not found"
            }
        
        return json.dumps(result)
    
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "handle": handle
        }
        return json.dumps(error_result)


def create_catalog_tools(supabase_client: SupabaseClient) -> List[Any]:
    """Create catalog tools with Supabase client injected.
    
    Args:
        supabase_client: Initialized Supabase client
        
    Returns:
        List of configured tools
    """
    # Inject the supabase client into each tool
    search_embedding._supabase_client = supabase_client
    filter_products._supabase_client = supabase_client
    
    return [
        filter_products,
        search_embedding
    ]
