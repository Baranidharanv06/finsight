import os
import time

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClientf

from backend.acre import ClearanceLevel

AUTH_MODE = os.getenv("AUTH_MODE", "local").lower()
LOCAL_JWT_SECRET = os.getenv("LOCAL_JWT_SECRET", "dev-only-secret-change-me-0123456789abcdef")

COGNITO_REGION = os.getenv("COGNITO_REGION", "ap-south-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")

_jwks_client = None


def _issuer() -> str:
    return f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{_issuer()}/.well-known/jwks.json")
    return _jwks_clientf

def decode_token(token: str) -> dict:
    """Verify signature and expiry, return the claims. Raises jwt errors."""
    if AUTH_MODE == "cognito":
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=_issuer(),
            options={"verify_aud": False},
        )
        token_use = claims.get("token_use")
        if token_use == "access" and claims.get("client_id") != COGNITO_CLIENT_ID:
            raise jwt.InvalidTokenError("wrong client_id")
        if token_use == "id" and claims.get("aud") != COGNITO_CLIENT_ID:
            raise jwt.InvalidTokenError("wrong audience")
        return claims

    return jwt.decode(token, LOCAL_JWT_SECRET, algorithms=["HS256"])


def clearance_from_claims(claims: dict) -> ClearanceLevel:
    groups = claims.get("cognito:groups", []) or []
    levels = [ClearanceLevel[g.upper()] for g in groups if g.upper() in ClearanceLevel.__members__]
    return max(levels) if levels else ClearanceLevel.GUEST


def get_clearance(authorization: str = Header(default=None)) -> ClearanceLevel:
    """FastAPI dependency: Authorization: Bearer <jwt>  ->  ClearanceLevel."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return clearance_from_claims(claims)


def make_local_token(group: str, email: str = "demo@vaultsight.local", ttl_seconds: int = 3600) -> str:
    """Dev helper: mint a token shaped like a Cognito one."""
    now = int(time.time())
    return jwt.encode(
        {
            "sub": email,
            "email": email,
            "cognito:groups": [group.upper()],
            "iat": now,
            "exp": now + ttl_seconds,
        },
        LOCAL_JWT_SECRET,
        algorithm="HS256",
    )


def get_caller(authorization: str = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "sub": str(claims.get("sub", "unknown")),
        "clearance": clearance_from_claims(claims),
    }
