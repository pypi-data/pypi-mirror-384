"""FastAPI integration helpers (optional extra).

Requires ``pip install empowernow-common[fastapi]`` which pulls FastAPI and
its dependencies.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..jwt import create_unified_validator, UnifiedTokenValidator
from ..identity import UniqueIdentity
from ..settings import settings
from ..utils.logging_config import get_logger
from ..jwt.errors import (
    UnknownIssuerError,
    TokenFormatError,
    TokenExpiredError,
    AudienceMismatchError,
    NetworkError,
    DiscoveryError,
    JWKSFetchError,
    IntrospectionError,
    TokenTypeRejectedError,
    SignatureValidationError,
    IssuerMismatchError,
    IntrospectionRejectedError,
    ConfigurationError,
)

__all__ = ["build_auth_dependency", "request_context", "bearer_scheme"]

# Single HTTPBearer instance exposed for proper FastAPI/OpenAPI integration
bearer_scheme = HTTPBearer(auto_error=False)
logger = get_logger(__name__)


# ------------------------------------------------------------------
# Request context extractor
# ------------------------------------------------------------------


_SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "proxy-authorization"}


async def request_context(
    request: Request,
    *,
    include_headers: bool = False,
    include_body: bool = False,
    max_body_bytes: int = 2048,
) -> Dict[str, Any]:
    """Return a context dict suitable for `EnhancedPDP.check()`.

    Parameters
    ----------
    include_headers:
        When *True* includes **masked** request headers.
    include_body:
        When *True* includes raw body bytes capped at *max_body_bytes*.
    max_body_bytes:
        Maximum number of bytes to read from the request body (default 2 KiB).
    """

    ctx: Dict[str, Any] = {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "query_params": dict(request.query_params) if request.query_params else {},
    }

    if include_headers:
        masked_headers: Dict[str, str] = {}
        for k, v in request.headers.items():
            if k.lower() in _SENSITIVE_HEADERS:
                masked_headers[k] = "***redacted***"
            else:
                masked_headers[k] = v
        ctx["headers"] = masked_headers

    if include_body:
        try:
            body_bytes = await request.body()
            if len(body_bytes) > max_body_bytes:
                body_bytes = body_bytes[:max_body_bytes] + b"..."
            ctx["body"] = body_bytes.decode(errors="replace")
        except Exception as exc:  # pragma: no cover – edge-case
            logger.debug("could not read request body", exc_info=exc)

    return ctx


def build_auth_dependency(
    validator: Optional[UnifiedTokenValidator] = None,
    idps_yaml_path: Optional[str] = None,
    default_idp_for_opaque: Optional[str] = None,
    require_token: bool = True,
    enable_authentication: Optional[bool] = None,
) -> Callable[[Request], Awaitable[Optional[Dict[str, Any]]]]:
    """
    Create a FastAPI dependency for token validation with development mode support.
    
    Args:
        validator: Pre-configured validator instance (if not provided, one will be created)
        idps_yaml_path: Path to IdP config file (required if validator not provided)
        default_idp_for_opaque: Default IdP for opaque tokens
        require_token: Whether to require a token (if False, returns None for missing token)
        enable_authentication: Override authentication enablement (defaults to ENABLE_AUTHENTICATION env var)
        
    Returns:
        FastAPI dependency function
        
    Example:
        from fastapi import FastAPI, Depends
        from empowernow_common.fastapi import build_auth_dependency
        
        app = FastAPI()
        
        auth = build_auth_dependency(
            idps_yaml_path="ServiceConfigs/idps.yaml",
            default_idp_for_opaque="legacy"
        )
        
        @app.get("/protected")
        async def protected_route(user: dict = Depends(auth)):
            return {"user": user["sub"]}
    """
    # Check authentication enablement
    auth_enabled = enable_authentication if enable_authentication is not None else settings.enable_authentication

    async def token_validator_dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    ) -> Optional[Dict[str, Any]]:
        """FastAPI dependency that validates tokens and returns claims."""
        
        # Development/testing mode - skip authentication
        if not auth_enabled:
            logger.info("Authentication skipped (ENABLE_AUTHENTICATION=0)")
            return {"sub": "anonymous", "unique_id": "auth:anon", "roles": [], "permissions": []}
        
        # Create validator on first use if not provided (lazy initialization)
        nonlocal validator
        if validator is None:
            validator = create_unified_validator(
                idps_yaml_path=idps_yaml_path,
                default_idp_for_opaque=default_idp_for_opaque,
                auto_reload=True
            )
        
        # Missing credentials
        if not credentials:
            if require_token:
                raise HTTPException(
                    status_code=401,
                    detail="Bearer token required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        try:
            # Validate token using unified validator
            claims = await validator.validate_token(credentials.credentials)

            # Add unique_id using UniqueIdentity
            if "iss" in claims and "sub" in claims:
                # Get IdP name from claims (added by validators)
                idp_name = claims.get("idp_name", "unknown")
                claims["unique_id"] = UniqueIdentity(
                    issuer=claims["iss"],
                    subject=claims["sub"],
                    idp_name=idp_name
                ).value

            # Set normalized_claims on request.state for middleware/logging access
            if "roles" in claims or "permissions" in claims:
                request.state.normalized_claims = {
                    "roles": claims.get("roles", []),
                    "permissions": claims.get("permissions", [])
                }

            return claims
            
        except TokenExpiredError as e:
            logger.warning("Token expired: %s", str(e))
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except (TokenFormatError, TokenTypeRejectedError, SignatureValidationError,
                AudienceMismatchError, IssuerMismatchError, IntrospectionRejectedError) as e:
            logger.warning("Invalid token: %s", str(e))
            raise HTTPException(
                status_code=401,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except UnknownIssuerError as e:
            logger.warning("Unknown issuer: %s", str(e))
            raise HTTPException(
                status_code=401,
                detail="Unknown token issuer",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except (NetworkError, DiscoveryError, JWKSFetchError, IntrospectionError) as e:
            # Network/upstream failures should return 502 Bad Gateway
            logger.error("Upstream validation failed: %s", str(e))
            raise HTTPException(
                status_code=502,
                detail="Token validation service unavailable"
            ) from e
        except ConfigurationError as e:
            logger.error("Configuration error: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail="Service configuration error"
            ) from e
        except Exception as e:
            logger.error("Unexpected validation error: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail="Internal validation error"
            ) from e

    return token_validator_dependency
