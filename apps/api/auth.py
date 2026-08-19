"""Optional Keycloak JWT verification for the KappaLake API."""
import os

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
REALM = os.getenv("KEYCLOAK_REALM", "kappalake")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"

_client = None


def _jwk_client():
    global _client
    if _client is None:
        _client = PyJWKClient(f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs")
    return _client


def verify_token(token: str) -> dict:
    signing_key = _jwk_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )


def get_current_user(request: Request):
    """FastAPI dependency: validates the bearer token when auth is enabled."""
    if not AUTH_ENABLED:
        return {"sub": "local", "preferred_username": "local"}
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return verify_token(auth[7:])
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
