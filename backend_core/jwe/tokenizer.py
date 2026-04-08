import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jwcrypto import jwk, jwe
from jwcrypto.jwk import JWK
from jwcrypto.jwe import JWE
from jwcrypto.common import json_decode, json_encode

DEFAULT_ISSUER = "cm_saas"
DEFAULT_AUDIENCE = "fastapi_microservice"
DEFAULT_EXPIRE_MINUTES = 30
DEFAULT_GRACE_WINDOW_SECONDS = 120


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def _create_jwe_token(payload: Dict[str, Any], jwk_key: JWK) -> str:
    headers = {"alg": "A256KW", "enc": "A256GCM", "typ": "JWE"}
    
    jwe = JWE(json_encode(payload).encode(), protected=json_encode(headers))
    jwe.add_recipient(jwk_key)
    
    return jwe.serialize(compact=True)


def get_jwk_key(secret_key: str) -> JWK:
    return JWK(kty="oct", k=secret_key)


def create_auth_jwe_token(
    store_hash: str,
    session_id: Optional[str] = None,
    user_role: str = "admin",
    secret_key: str = None,
    issuer: str = DEFAULT_ISSUER,
    audience: str = DEFAULT_AUDIENCE,
    expire_minutes: int = DEFAULT_EXPIRE_MINUTES
) -> Dict[str, Any]:
    """
    Create a JWE token with payload containing auth data.
    
    Args:
        store_hash: The store identifier
        session_id: Optional session ID, auto-generated if not provided
        user_role: User role (default: "admin")
        secret_key: JWE secret key for encryption
        issuer: Token issuer (default: "cm_saas")
        audience: Token audience (default: "fastapi_microservice")
        expire_minutes: Token expiration in minutes (default: 30)
    
    Returns:
        Dict containing token, expires_in, and expiresAt
    """
    if secret_key is None:
        raise ValueError("secret_key is required")
    
    now = datetime.now(timezone.utc)
    
    if session_id is None:
        session_id = f"session_{int(now.timestamp())}_{uuid.uuid4().hex[:8]}"
    
    payload = {
        "store_hash": store_hash,
        "session_id": session_id,
        "user_role": user_role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expire_minutes)).timestamp()),
        "iss": issuer,
        "aud": audience
    }
    
    jwk_key = get_jwk_key(secret_key)
    token = _create_jwe_token(payload, jwk_key)
    
    return {
        "token": token,
        "expires_in": int((now + timedelta(minutes=expire_minutes)).timestamp()),
        "expiresAt": (now + timedelta(minutes=expire_minutes)).isoformat()
    }


def decrypt_auth_jwe_token(token: str, secret_key: str = None) -> Dict[str, Any]:
    """
    Decrypt a JWE token and return the payload.
    
    Args:
        token: The JWE token string
        secret_key: JWE secret key for decryption
    
    Returns:
        Dict containing the decrypted payload
    """
    if secret_key is None:
        raise ValueError("secret_key is required")
    
    jwk_key = get_jwk_key(secret_key)
    jwe_obj = JWE()
    
    jwe_obj.deserialize(token, key=jwk_key)
    payload = json.loads(jwe_obj.payload.decode())
    return payload