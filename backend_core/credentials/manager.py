from typing import Any, Dict, Optional
from datetime import datetime, timezone
import json
import logging

from ..saas_app import SaasAppAPIClient
from ..jwe import decrypt_auth_jwe_token as decrypt_jwe_token
from starlette.requests import Request as StarletteRequest

logger = logging.getLogger(__name__)

CREDENTIALS_FIELDS = [
    "id", "store_hash", "access_token", "api_url", "api_version",
    "client_id", "client_secret", "service_id", "program_id",
    "username", "password_encrypted", "vehicle_api"
]


class CredentialManager:
    def __init__(
        self,
        jwe_secret_key: str,
        saas_client: SaasAppAPIClient
    ):
        self.jwe_secret_key = jwe_secret_key
        self.saas_client = saas_client

    def _store_in_session(
        self,
        request: StarletteRequest,
        store_hash: str,
        decrypted_data: Dict[str, Any],
        jwe_token: Optional[str] = None,
        app_name: Optional[str] = None,
        table_name: str = "credentials"
    ):
        """Store credentials, allowed_domains, and metadata in session."""
        session_data = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "app_name": app_name,
            "table_name": table_name,
            "jwe_token": jwe_token
        }
        
        credentials = {k: v for k, v in decrypted_data.items() if k in CREDENTIALS_FIELDS}
        if credentials:
            session_data["credentials"] = credentials
            logger.info(f"Credentials found for store_hash: {store_hash}")
        
        settings_json = decrypted_data.get("settings")
        if settings_json:
            try:
                if isinstance(settings_json, str):
                    settings_obj = json.loads(settings_json)
                else:
                    settings_obj = settings_json
                
                allowed_domains_str = settings_obj.get("allowed_domains", "")
                logger.info(f"Settings JSON parsed, allowed_domains: {allowed_domains_str}")
                if allowed_domains_str:
                    domains = [d.strip() for d in allowed_domains_str.split(",") if d.strip()]
                    if domains:
                        session_data["allowed_domains"] = domains
                        logger.info(f"Domains extracted: {domains}")
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse settings JSON: {settings_json}, error: {e}")
        
        if session_data:
            request.session[store_hash] = session_data
            logger.info(f"Stored session data for store_hash: {store_hash}, keys: {list(session_data.keys())}")
        else:
            logger.warning(f"No session data to store for store_hash: {store_hash}")

    async def get_bigcommerce_credentials(
        self,
        request: StarletteRequest,
        app_name: str,
        store_hash: str
    ) -> Dict[str, Any]:
        """
        Fetch BigCommerce credentials from SaaS app.
        
        Flow:
        1. Check session for cached credentials
        2. If not cached → call SaaS API to get credentials
        3. Decrypt JWE token to get store_hash and access_token
        4. Store in session for subsequent calls
        5. Return credentials
        
        Args:
            request: Starlette Request object (for session access)
            app_name: Application name
            store_hash: BigCommerce store hash
            
        Returns:
            Dict with store_hash and access_token
        """
        session_data = request.session.get(store_hash, {})
        
        if session_data:
            jwe_token = session_data.get("jwe_token")
            if jwe_token:
                try:
                    bc_credentials = decrypt_jwe_token(jwe_token, self.jwe_secret_key)
                    return {
                        "store_hash": bc_credentials.get("store_hash"),
                        "access_token": bc_credentials.get("access_token")
                    }
                except Exception as e:
                    logger.warning(f"Failed to decrypt cached jwe_token: {e}")
            
            credentials = session_data.get("credentials", {})
            if credentials.get("store_hash") and credentials.get("access_token"):
                return {
                    "store_hash": credentials.get("store_hash"),
                    "access_token": credentials.get("access_token")
                }
        
        try:
            data = await self.saas_client.get_data(app_name, store_hash, "credentials")
            logger.info(f"data_micro response keys: {list(data.keys())}")
            
            if app_name in data:
                app_data = data.get(app_name, {})
                jwe_token_bc = app_data.get("jwe_token")
                
                if jwe_token_bc:
                    decrypted_data = decrypt_jwe_token(jwe_token_bc, self.jwe_secret_key)
                    logger.info(f"Decrypted credentials keys: {decrypted_data.keys()}")
                    
                    self._store_in_session(
                        request, store_hash, decrypted_data,
                        jwe_token=jwe_token_bc, app_name=app_name, table_name="credentials"
                    )
                    
                    return {
                        "store_hash": decrypted_data.get("store_hash"),
                        "access_token": decrypted_data.get("access_token")
                    }
                
                return {
                    "store_hash": app_data.get("store_hash"),
                    "access_token": app_data.get("access_token")
                }
            
            bc_data = data.get("bc_data", {})
            jwe_token_bc = bc_data.get("jwe_token") if bc_data else None
            logger.info(f"bc_data from root: {bc_data}")
            
            if jwe_token_bc:
                bc_credentials = decrypt_jwe_token(jwe_token_bc, self.jwe_secret_key)
                logger.info(f"BC credentials: {bc_credentials}")
                
                self._store_in_session(
                    request, store_hash, bc_credentials,
                    jwe_token=jwe_token_bc, app_name=app_name, table_name="credentials"
                )
                
                return {
                    "store_hash": bc_credentials.get("store_hash"),
                    "access_token": bc_credentials.get("access_token")
                }
            
            raise ValueError("BigCommerce credentials not found in response")
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get BigCommerce credentials: {e}")
            raise