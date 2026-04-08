from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from ..jwe import (
    create_auth_jwe_token,
    decrypt_auth_jwe_token,
    validate_jwe_payload,
    refresh_auth_token,
    is_token_expiring_soon
)
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

security = HTTPBearer()


class LoginRequestSchema(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenRefreshRequestSchema(BaseModel):
    token: Optional[str] = Field(None, description="JWE token to refresh")


class ResponseModel(BaseModel):
    success: bool
    data: Any = None
    message: str = ""


def _get_authorization_header(request: Request) -> Optional[str]:
    """Get Authorization header from request."""
    return request.headers.get("Authorization")


async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    secret_key: str = None,
    issuer: str = "cm_saas",
    audience: str = "fastapi_microservice"
) -> Dict[str, Any]:
    """
    FastAPI dependency to verify JWE token from Authorization header.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = decrypt_auth_jwe_token(token, secret_key=secret_key)
        
        if not validate_jwe_payload(payload, issuer=issuer, audience=audience):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        store_hash = payload.get("store_hash")
        if store_hash:
            request.state.store_hash = store_hash
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def create_auth_router(
    secret_key: str,
    issuer: str = "cm_saas",
    audience: str = "fastapi_microservice",
    expire_minutes: int = 30,
    grace_window_seconds: int = 120,
    auth_username: str = "admin",
    auth_password: str = "admin"
):
    """
    Create auth router with custom settings.
    
    Args:
        secret_key: JWE secret key
        issuer: Token issuer
        audience: Token audience
        expire_minutes: Token expiration in minutes
        grace_window_seconds: Grace window for token refresh
        auth_username: Username for login
        auth_password: Password for login
    
    Returns:
        FastAPI router
    """
    
    @router.post("/login", response_model=ResponseModel)
    async def login(request: LoginRequestSchema):
        """Authenticate a user and return JWE token."""
        if request.username != auth_username or request.password != auth_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        store_hash = "demo_store"
        token_data = create_auth_jwe_token(
            store_hash=store_hash,
            secret_key=secret_key,
            issuer=issuer,
            audience=audience,
            expire_minutes=expire_minutes
        )
        
        logger.info(f"User {request.username} logged in successfully")
        
        return ResponseModel(
            success=True,
            data=token_data,
            message="Login successful"
        )

    @router.post("/refresh", response_model=ResponseModel)
    async def refresh_token(
        request: Request,
        body: Optional[TokenRefreshRequestSchema] = None
    ):
        """Refresh an expiring JWE token."""
        authorization = _get_authorization_header(request)
        existing_token = None
        
        if authorization and authorization.startswith("Bearer "):
            existing_token = authorization[7:]
        elif body and body.token:
            existing_token = body.token
        
        if not existing_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required. Pass in Authorization header or request body.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            payload = decrypt_auth_jwe_token(existing_token, secret_key=secret_key)
            
            if not validate_jwe_payload(payload, issuer=issuer, audience=audience):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: Token payload validation failed"
                )
            
            expires_in = payload.get("exp", 0)
            if expires_in and is_token_expiring_soon(expires_in, grace_window=grace_window_seconds):
                new_token_data = refresh_auth_token(
                    existing_token,
                    secret_key=secret_key,
                    issuer=issuer,
                    audience=audience
                )
                logger.info(f"Token refreshed for store: {payload.get('store_hash')}")
                return ResponseModel(
                    success=True,
                    data=new_token_data,
                    message="Token refreshed successfully"
                )
            
            return ResponseModel(
                success=True,
                data={"token": existing_token, "expires_in": expires_in},
                message="Token still valid"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

    @router.post("/validate-session", response_model=ResponseModel)
    async def validate_session(request: Request):
        """Validate if a JWE token session is still valid."""
        authorization = _get_authorization_header(request)
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = authorization[7:]
        
        try:
            payload = decrypt_auth_jwe_token(token, secret_key=secret_key)
            
            if not validate_jwe_payload(payload, issuer=issuer, audience=audience):
                expires_in = payload.get("exp", 0)
                expires_at = datetime.fromtimestamp(expires_in, tz=timezone.utc).isoformat() if expires_in else None
                return ResponseModel(
                    success=True,
                    data={
                        "token": f"Bearer {token}",
                        "expiresAt": expires_at,
                        "valid": False
                    },
                    message="Session expired"
                )
            
            expires_in = payload.get("exp", 0)
            expires_at = datetime.fromtimestamp(expires_in, tz=timezone.utc).isoformat() if expires_in else None
            
            return ResponseModel(
                success=True,
                data={
                    "token": f"Bearer {token}",
                    "expiresAt": expires_at,
                    "valid": True
                },
                message="Session valid"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return ResponseModel(
                success=True,
                data={
                    "token": f"Bearer {token}" if token else None,
                    "expiresAt": None,
                    "valid": False
                },
                message="Session invalid"
            )
    
    return router