from datetime import datetime, timezone
from typing import Any, Dict

DEFAULT_ISSUER = "cm_saas"
DEFAULT_AUDIENCE = "fastapi_microservice"
DEFAULT_GRACE_WINDOW_SECONDS = 120


def validate_jwe_payload(
    payload: Dict[str, Any],
    issuer: str = DEFAULT_ISSUER,
    audience: str = DEFAULT_AUDIENCE
) -> bool:
    """
    Validate JWE token payload.
    
    Args:
        payload: The decrypted token payload
        issuer: Expected issuer
        audience: Expected audience
    
    Returns:
        True if payload is valid, False otherwise
    """
    now = int(datetime.now(timezone.utc).timestamp())
    
    if "exp" in payload and payload["exp"] < now:
        return False
    
    if "iss" in payload and payload["iss"] != issuer:
        return False
    
    if "aud" in payload and payload["aud"] != audience:
        return False
    
    if "store_hash" not in payload:
        return False
    
    return True


def is_token_expiring_soon(expires_in: int, grace_window: int = DEFAULT_GRACE_WINDOW_SECONDS) -> bool:
    """
    Check if a token is expiring soon.
    
    Args:
        expires_in: Unix timestamp of token expiration
        grace_window: Seconds before expiration to consider "expiring soon"
    
    Returns:
        True if token expires within grace window
    """
    now = int(datetime.now(timezone.utc).timestamp())
    return (expires_in - now) <= grace_window