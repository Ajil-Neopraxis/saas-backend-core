from datetime import datetime, timezone
from typing import Any, Dict

from .tokenizer import create_auth_jwe_token, decrypt_auth_jwe_token
from .validator import validate_jwe_payload, is_token_expiring_soon


def refresh_auth_token(
    token: str,
    secret_key: str,
    issuer: str = "cm_saas",
    audience: str = "fastapi_microservice"
) -> Dict[str, Any]:
    """
    Refresh an expiring JWE token.
    
    Args:
        token: The current JWE token
        secret_key: JWE secret key
        issuer: Token issuer
        audience: Token audience
    
    Returns:
        Dict containing new token data or current token if still valid
    """
    payload = decrypt_auth_jwe_token(token, secret_key)
    
    if not validate_jwe_payload(payload, issuer, audience):
        raise ValueError("Invalid token payload")
    
    expires_in = payload.get("exp", 0)
    if expires_in and is_token_expiring_soon(expires_in):
        return create_auth_jwe_token(
            store_hash=payload.get("store_hash", ""),
            session_id=payload.get("session_id"),
            user_role=payload.get("user_role", "admin"),
            secret_key=secret_key,
            issuer=issuer,
            audience=audience
        )
    
    return {
        "token": token,
        "expires_in": expires_in,
        "expiresAt": datetime.fromtimestamp(expires_in, timezone.utc).isoformat() if expires_in else None
    }