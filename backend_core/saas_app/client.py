from typing import Any, Dict, Optional

from ..api import BaseAPIClient


class SaasAppAPIClient(BaseAPIClient):
    """
    Client for communicating with the SaaS platform API.
    """
    
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        language: str = "en"
    ):
        super().__init__(base_url=base_url, token=token, language=language)
    
    async def get_data(
        self,
        app_name: str,
        store_hash: str,
        table_name: str = "credentials",
        decrypt: bool = False
    ) -> Dict[str, Any]:
        params = {
            "app_name": app_name,
            "table_name": table_name,
            "store_hash": store_hash
        }
        
        if decrypt:
            params["decrypt"] = "true"
        
        return await self.get("/api/v1/apps/data_micro/", params=params)
    
    async def create(
        self,
        app_name: str,
        table_name: str,
        store_hash: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.post(
            "/api/v1/apps/data_micro/",
            json={
                "app_name": app_name,
                "table_name": table_name,
                "store_hash": store_hash,
                "data": data
            }
        )
    
    async def update(
        self,
        record_id: int,
        app_name: str,
        table_name: str,
        store_hash: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.put(
            f"/api/v1/apps/data_micro/{record_id}/",
            json={
                "app_name": app_name,
                "table_name": table_name,
                "store_hash": store_hash,
                "data": data
            }
        )
    
    async def delete(
        self,
        record_id: int,
        app_name: str,
        table_name: str,
        store_hash: str
    ) -> Dict[str, Any]:
        params = {
            "app_name": app_name,
            "table_name": table_name,
            "store_hash": store_hash
        }
        return await self.delete(f"/api/v1/apps/data_micro/{record_id}/", params=params)