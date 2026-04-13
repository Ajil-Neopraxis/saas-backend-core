from typing import Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class ThirdPartyAPIClient:
    """
    Client for third-party/external vendor API calls.
    """

    def __init__(self):
        pass

    async def get_products(
        self,
        api_url: str,
        api_version: str,
        username: str,
        password_encrypted: str,
        product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get products from third-party API.

        Args:
            api_url: Base URL of the third-party API
            api_version: API version (e.g., v1, v2)
            username: Username for authentication
            password_encrypted: Encrypted password for authentication
            product_name: Optional product name to search for

        Returns:
            Dict containing products data
        """
        url = f"{api_url}/{api_version}/get_products"
        
        payload = {
            "username": username,
            "password_encrypted": password_encrypted
        }
        
        headers = {}
        if product_name:
            headers["p_name"] = product_name
        
        logger.info(f"Calling third-party API: {url}")
        logger.info(f"Third-party API payload: {payload}")
        logger.info(f"Third-party API headers: {headers}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Third-party API error: {response.status_code} - {error_text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Third-party API response: {result}")
            return result


def create_third_party_client() -> ThirdPartyAPIClient:
    """
    Factory function to create ThirdPartyAPIClient.

    Returns:
        ThirdPartyAPIClient instance
    """
    return ThirdPartyAPIClient()