"""Supabase client for product search and filtering."""

import json
from typing import Any, Dict, List, Optional, Union
import requests
from ..types.core import ProductResult, APIError, ConfigurationError


class SupabaseClient:
    """Client for interacting with Supabase functions."""
    
    def __init__(self, supabase_functions_url: str, gpt_actions_api_key: str):
        """Initialize the Supabase client.
        
        Args:
            supabase_functions_url: Supabase Functions URL
            gpt_actions_api_key: GPT Actions API key
        """
        self.supabase_functions_url = supabase_functions_url.rstrip('/')
        self.gpt_actions_api_key = gpt_actions_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {gpt_actions_api_key}'
        })
    
    def _post_json(self, endpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to Supabase function.
        
        Args:
            endpoint: API endpoint
            body: Request body
            
        Returns:
            Response data
            
        Raises:
            APIError: If the request fails
        """
        # The supabase_functions_url already includes the functions path
        # So we just append the endpoint directly
        url = f"{self.supabase_functions_url}/{endpoint}"
        
        try:
            response = self.session.post(url, json=body, timeout=30)
            
            if not response.ok:
                error_text = response.text
                raise APIError(
                    f"Supabase API error: {response.status_code} {response.reason}",
                    response.status_code,
                    {"endpoint": endpoint, "body": body, "error_text": error_text}
                )
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise APIError(
                f"Network error calling {endpoint}",
                0,
                {"endpoint": endpoint, "body": body, "original_error": str(e)}
            )
        except json.JSONDecodeError as e:
            raise APIError(
                f"Invalid JSON response from {endpoint}",
                0,
                {"endpoint": endpoint, "body": body, "original_error": str(e)}
            )
    
    def search_products(
        self, 
        query: str, 
        limit: int = 20, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ProductResult]:
        """Search for products.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            filters: Additional filters
            
        Returns:
            List of product results
        """
        body = {
            "query": query,
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            body["filters"] = filters
        
        try:
            response = self._post_json("/search-embedding", body)
            products_data = response.get("results", [])
            
            return [ProductResult(**product) for product in products_data]
        
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(
                f"Error searching products: {str(e)}",
                0,
                {"query": query, "limit": limit, "offset": offset, "filters": filters}
            )
    
    def filter_products(
        self,
        filters: Dict[str, Any],
        limit: int = 20,
        offset: int = 0
    ) -> List[ProductResult]:
        """Filter products by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of filtered product results
        """
        body = {
            "filters": filters,
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = self._post_json("/filter-products", body)
            products_data = response.get("results", [])
            
            return [ProductResult(**product) for product in products_data]
        
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(
                f"Error filtering products: {str(e)}",
                0,
                {"filters": filters, "limit": limit, "offset": offset}
            )
    
    def discover_products(
        self,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[ProductResult]:
        """Discover products based on user preferences.
        
        Args:
            user_preferences: User preferences for discovery
            limit: Maximum number of results
            
        Returns:
            List of discovered product results
        """
        body = {
            "limit": limit
        }
        
        if user_preferences:
            body["user_preferences"] = user_preferences
        
        try:
            response = self._post_json("/discover-products", body)
            products_data = response.get("results", [])
            
            return [ProductResult(**product) for product in products_data]
        
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(
                f"Error discovering products: {str(e)}",
                0,
                {"user_preferences": user_preferences, "limit": limit}
            )
    
    def get_product_by_handle(self, handle: str) -> Optional[ProductResult]:
        """Get a specific product by handle.
        
        Args:
            handle: Product handle
            
        Returns:
            Product result or None if not found
        """
        body = {"handle": handle}
        
        try:
            response = self._post_json("/get-product", body)
            product_data = response.get("product")
            
            if product_data:
                return ProductResult(**product_data)
            return None
        
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(
                f"Error getting product by handle: {str(e)}",
                0,
                {"handle": handle}
            )
    
    def health_check(self) -> bool:
        """Check if the Supabase client is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple search to verify the connection works
            # This is more reliable than a dedicated health endpoint
            response = self._post_json("search-embedding", {
                "query": "test",
                "limit": 1
            })
            return "results" in response
        except Exception:
            return False
