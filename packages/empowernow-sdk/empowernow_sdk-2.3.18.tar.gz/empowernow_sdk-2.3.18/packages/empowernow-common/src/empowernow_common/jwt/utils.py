"""Simple, dependency-free helpers to look at JWT structures without verifying.

These functions do *not* validate signatures or claim sets – they are only
meant for routing logic, logging or debugging where cryptographic integrity
is either ensured upstream or not required.
"""

from __future__ import annotations

import base64
import json
import hashlib
import hmac
import os
import time
from typing import Any, Dict, Tuple, Optional
from collections import OrderedDict
from threading import Lock

__all__ = [
    "peek_header", 
    "peek_payload", 
    "peek_header_and_payload",
    "canonicalize_issuer",
    "hmac_token_key",
    "LRUTTLCache",
    "normalize_token_claims",
]


def _b64url_decode(part: str) -> bytes:
    # Add padding if missing
    padded = part + "=" * (-len(part) % 4)
    return base64.urlsafe_b64decode(padded)


def peek_header(token: str) -> Dict[str, Any]:
    """Return decoded JWT header as dict without verifying signature."""

    try:
        header_b64 = token.split(".", 2)[0]
        return json.loads(_b64url_decode(header_b64))
    except (ValueError, IndexError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JWT") from exc


def peek_payload(token: str) -> Dict[str, Any]:
    """Return decoded JWT payload (claims) as dict without verifying."""

    try:
        payload_b64 = token.split(".", 2)[1]
        return json.loads(_b64url_decode(payload_b64))
    except (ValueError, IndexError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JWT") from exc


def peek_header_and_payload(token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return both header and payload without verification."""
    return peek_header(token), peek_payload(token)


def canonicalize_issuer(issuer: Optional[str]) -> Optional[str]:
    """
    Canonicalize issuer URL by stripping trailing slash.
    
    This ensures consistent issuer matching across different representations.
    """
    if issuer:
        return issuer.rstrip('/')
    return issuer


# Generate a boot-time secret for HMAC operations
_HMAC_SECRET = os.urandom(32)


def hmac_token_key(token: str) -> str:
    """
    Generate a secure cache key for a token using HMAC.
    
    This prevents token values from being stored directly in cache keys,
    which could be logged or exposed in monitoring systems.
    """
    mac = hmac.new(_HMAC_SECRET, token.encode('utf-8'), hashlib.sha256)
    return mac.hexdigest()


class LRUTTLCache:
    """
    Simple LRU cache with TTL support for discovery and JWKS caching.
    
    Thread-safe implementation using OrderedDict and Lock.
    """
    
    def __init__(self, maxsize: int = 128, default_ttl: int = 1800):
        """
        Initialize cache.
        
        Args:
            maxsize: Maximum number of entries (default 128)
            default_ttl: Default TTL in seconds (default 30 minutes)
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            if time.time() > expiry:
                # Expired - remove it
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            # Remove oldest if at capacity
            if key not in self._cache and len(self._cache) >= self.maxsize:
                self._cache.popitem(last=False)  # Remove oldest
            
            expiry = time.time() + ttl
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Return current cache size."""
        with self._lock:
            return len(self._cache)


def normalize_token_claims(
    claims: Dict[str, Any],
    issuer: str,
    validation_method: str,
    idp_name: str
) -> Dict[str, Any]:
    """
    Normalize token claims to consistent format per PDF spec.
    
    Args:
        claims: Raw claims from token validation
        issuer: The token issuer
        validation_method: Either "jwks" or "introspection"
        idp_name: Name of the IdP configuration
        
    Returns:
        Normalized claims dictionary with standard fields
    """
    # Extract scopes
    scopes = []
    if "scp" in claims and isinstance(claims["scp"], list):
        scopes = claims["scp"]
    elif "scope" in claims and isinstance(claims["scope"], str):
        scopes = claims["scope"].split()
    
    # Extract subject (sub or username)
    subject = claims.get("sub") or claims.get("username", "unknown")
    
    # Extract client_id (azp for JWT or client_id for introspection)
    client_id = claims.get("azp") or claims.get("client_id")
    
    # Extract expires_at as epoch seconds
    expires_at = claims.get("exp")
    
    return {
        **claims,
        "issuer": issuer,
        "subject": subject,
        "client_id": client_id,
        "expires_at": expires_at,
        "scopes": scopes,
        "roles": [],  # Will be populated by ClaimsMapper if configured
        "permissions": [],  # Will be populated by ClaimsMapper if configured
        "validation_method": validation_method,
        "idp_name": idp_name,
    }
