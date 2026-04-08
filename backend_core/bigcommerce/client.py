import aiohttp
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BigCommerceClient:
    """
    Client for BigCommerce API operations.
    """
    
    def __init__(self, store_hash: str, access_token: str):
        self.store_hash = store_hash
        self.access_token = access_token
        self.base_url = f"https://api.bigcommerce.com/stores/{store_hash}"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Auth-Token": self.access_token
        }
    
    async def get_products(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get products from BigCommerce catalog.
        
        Args:
            page: Page number
            limit: Number of results per page
        
        Returns:
            Dict containing products data and meta
        """
        url = f"{self.base_url}/v3/catalog/products"
        params = {"page": page, "limit": limit}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self._get_headers()) as response:
                if response.status == 204:
                    return {"data": [], "meta": {}}
                response.raise_for_status()
                return await response.json()
    
    async def update_product(self, product_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product in BigCommerce.
        
        Args:
            product_id: The product ID
            data: Product data to update
        
        Returns:
            Updated product data
        """
        url = f"{self.base_url}/v3/catalog/products/{product_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=data, headers=self._get_headers()) as response:
                response.raise_for_status()
                return await response.json()
    
    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get a single product by ID."""
        url = f"{self.base_url}/v3/catalog/products/{product_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                response.raise_for_status()
                return await response.json()
    
    async def get_categories(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get categories from BigCommerce."""
        url = f"{self.base_url}/v3/catalog/categories"
        params = {"page": page, "limit": limit}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self._get_headers()) as response:
                if response.status == 204:
                    return {"data": [], "meta": {}}
                response.raise_for_status()
                return await response.json()


def create_bigcommerce_client(store_hash: str, access_token: str) -> BigCommerceClient:
    """
    Factory function to create BigCommerceClient.
    
    Args:
        store_hash: BigCommerce store hash
        access_token: BigCommerce API access token
    
    Returns:
        BigCommerceClient instance
    """
    return BigCommerceClient(store_hash, access_token)