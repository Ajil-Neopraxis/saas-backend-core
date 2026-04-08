from typing import Any, Dict, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


def get_auth_headers(
    token: Optional[str] = None,
    language: str = "en"
) -> Dict[str, str]:
    """
    Get common auth headers for API requests.
    
    Args:
        token: Optional bearer token
        language: Language for requests
    
    Returns:
        Dict of headers
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Cookie": f"seller_apps_language={language}"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class BaseAPIClient:
    """
    Base HTTP client with retry logic and interceptors.
    """
    
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        language: str = "en",
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.language = language
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _get_headers(self) -> Dict[str, str]:
        return get_auth_headers(self.token, self.language)
    
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make GET request."""
        url = f"{self.base_url}{path}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=request_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make POST request."""
        url = f"{self.base_url}{path}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=json,
                data=data,
                headers=request_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make PUT request."""
        url = f"{self.base_url}{path}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                json=json,
                headers=request_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        url = f"{self.base_url}{path}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                params=params,
                headers=request_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()