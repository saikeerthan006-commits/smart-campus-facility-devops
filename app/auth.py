"""HMAC-signed bearer token authentication and strict server-side RBAC enforcement.
Secret keys are loaded from environment variables; role claims in request bodies are ignored.
"""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict

from fastapi import Header, HTTPException, status

from campus_model import ROLES


def get_secret_key() -> bytes:
    secret = os.environ.get("APP_SECRET_KEY", "dev-ephemeral-test-key-do-not-use-in-prod")
    return secret.encode("utf-8")


def create_signed_token(username: str, role: str, ttl_seconds: int = 3600) -> str:
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}")
    payload = {
        "sub": username,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    sig = hmac.new(get_secret_key(), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"


def verify_signed_token(token: str) -> Dict[str, str]:
    try:
        b64_payload, sig = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed bearer token",
        ) from exc
    expected_sig = hmac.new(
        get_secret_key(), b64_payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
        )
    padding = "=" * (-len(b64_payload) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(b64_payload + padding).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Corrupted token payload",
        ) from exc
    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    role = payload.get("role")
    if role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unrecognized role claim",
        )
    return {"username": payload["sub"], "role": role}


def get_current_actor(authorization: str = Header(default=None)) -> Dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization Bearer header",
        )
    token = authorization.split(" ", 1)[1].strip()
    return verify_signed_token(token)
