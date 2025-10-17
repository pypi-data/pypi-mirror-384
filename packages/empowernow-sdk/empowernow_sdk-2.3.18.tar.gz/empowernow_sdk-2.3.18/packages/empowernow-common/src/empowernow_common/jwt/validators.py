"""
Token validator implementations for different validation strategies.

This module provides concrete implementations of token validators:
- JWKSValidator: Local validation using public keys
- IntrospectionValidator: Remote validation via introspection endpoint
- UnifiedTokenValidator: Router that delegates to appropriate validator
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Protocol, List
from abc import abstractmethod

import httpx
import jwt

# Try to import Prometheus metrics if available
try:
    from prometheus_client import Counter, Histogram
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    Counter = None  # type: ignore
    Histogram = None  # type: ignore

# IdPCatalogue now in same module
from .config import IdPCatalogue
from ..oauth import HardenedOAuth
from ..oauth.claims import ClaimsMapper
from .config import ValidationStrategy, IdPConfig
from .errors import (
    ValidationError,
    UnknownIssuerError,
    TokenFormatError,
    TokenTypeRejectedError,
    SignatureValidationError,
    AudienceMismatchError,
    IssuerMismatchError,
    TokenExpiredError,
    IntrospectionRejectedError,
    JWKSFetchError,
    IntrospectionError,
    NetworkError,
    ConfigurationError,
)
from .lightweight_validator import LightweightValidator
from .utils import (
    peek_payload,
    peek_header_and_payload,
    canonicalize_issuer,
    hmac_token_key,
    LRUTTLCache,
    normalize_token_claims,
)

logger = logging.getLogger(__name__)

# Initialize metrics if available
if METRICS_AVAILABLE:
    jwt_validation_total = Counter(
        'jwt_validation_total',
        'Total JWT validation attempts',
        ['idp', 'strategy', 'result']
    )
    jwt_validation_errors_total = Counter(
        'jwt_validation_errors_total',
        'Total JWT validation errors',
        ['idp', 'strategy', 'error_type']
    )
    jwt_cache_hits_total = Counter(
        'jwt_cache_hits_total',
        'Total cache hits',
        ['cache_type']
    )
    jwt_introspection_calls_total = Counter(
        'jwt_introspection_calls_total',
        'Total introspection endpoint calls',
        ['idp']
    )
    jwt_validation_seconds = Histogram(
        'jwt_validation_seconds',
        'JWT validation duration in seconds',
        ['idp', 'strategy']
    )
    jwt_introspection_seconds = Histogram(
        'jwt_introspection_seconds',
        'Introspection call duration in seconds',
        ['idp']
    )
    jwt_nokid_total = Counter(
        'jwt_nokid_total',
        'JWTs without kid in header encountered',
        ['idp']
    )
else:
    # Dummy metrics when not available
    jwt_validation_total = None  # type: ignore[assignment]
    jwt_validation_errors_total = None  # type: ignore[assignment]
    jwt_cache_hits_total = None  # type: ignore[assignment]
    jwt_introspection_calls_total = None  # type: ignore[assignment]
    jwt_validation_seconds = None  # type: ignore[assignment]
    jwt_introspection_seconds = None  # type: ignore[assignment]
    jwt_nokid_total = None  # type: ignore[assignment]


class TokenValidator(Protocol):
    """Protocol for token validation implementations."""
    
    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a token and return normalized claims.
        
        Args:
            token: Token to validate
            
        Returns:
            Normalized claims dictionary
            
        Raises:
            ValidationError: Base class for all validation failures
        """
        ...


class JWKSValidator:
    """
    Validator that uses JWKS (public keys) for local JWT validation.
    
    Wraps LightweightValidator with proper error handling and configuration.
    """
    
    def __init__(self, idp_config: IdPConfig):
        """Initialize JWKS validator with IdP configuration."""
        if not idp_config.jwks:
            raise ConfigurationError(f"JWKS config required for IdP '{idp_config.name}'")

        self.idp_config = idp_config  # Store full config for audience access
        self.idp_name = idp_config.name
        self.expected_issuer = canonicalize_issuer(idp_config.issuer)
        self.jwks_config = idp_config.jwks
        self.accept_id_tokens = idp_config.accept_id_tokens
        
        # Store config for discovery
        self._jwks_url_override = self.jwks_config.jwks_url_override
        
        # Will be set by UnifiedTokenValidator to share caches
        self._shared_discovery_cache: Optional[LRUTTLCache] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # Create and store a single LightweightValidator instance
        self._validator: Optional[LightweightValidator] = None
        self._validator_jwks_url: Optional[str] = None
        
        logger.info(
            "Initialized JWKSValidator for IdP '%s': issuer=%s",
            self.idp_name,
            self.expected_issuer,
        )
    
    async def _get_jwks_url(self) -> str:
        """Get JWKS URL with discovery cache support."""
        if self._jwks_url_override:
            return self._jwks_url_override

        # Check discovery cache
        cache_key = f"discovery:{self.expected_issuer}"
        if self._shared_discovery_cache:
            cached_discovery = self._shared_discovery_cache.get(cache_key)
            if cached_discovery and "jwks_uri" in cached_discovery:
                logger.debug("Discovery cache hit for IdP '%s'", self.idp_name)
                if METRICS_AVAILABLE:
                    jwt_cache_hits_total.labels(cache_type='discovery').inc()
                return cached_discovery["jwks_uri"]

        # Perform OIDC discovery
        try:
            discovery_url = f"{self.expected_issuer}/.well-known/openid-configuration"
            logger.debug("Performing OIDC discovery for IdP '%s' at %s", self.idp_name, discovery_url)
            assert self._http_client is not None
            response = await self._http_client.get(discovery_url)
            response.raise_for_status()
            discovery_doc = response.json()
            jwks_uri = discovery_doc.get("jwks_uri")

            if jwks_uri:
                logger.debug("Discovered jwks_uri for IdP '%s': %s", self.idp_name, jwks_uri)
                # Cache discovery result for 30 minutes
                if self._shared_discovery_cache:
                    self._shared_discovery_cache.set(cache_key, {"jwks_uri": jwks_uri}, ttl=1800)
                return jwks_uri
        except Exception as e:
            logger.warning("OIDC discovery failed for IdP '%s': %s, falling back to well-known location",
                          self.idp_name, e)

        # Fallback to well-known location if discovery fails
        jwks_url = f"{self.expected_issuer}/.well-known/jwks.json"

        # Cache the fallback result
        if self._shared_discovery_cache:
            self._shared_discovery_cache.set(cache_key, {"jwks_uri": jwks_url}, ttl=1800)

        return jwks_url
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token using JWKS."""
        start_time = time.time()
        try:
            # Check if it's an ID token and reject if not accepted
            if not self.accept_id_tokens:
                try:
                    header, payload = peek_header_and_payload(token)
                    
                    # Track tokens without kid as required by PDF spec
                    if header.get("kid") is None and METRICS_AVAILABLE:
                        jwt_nokid_total.labels(idp=self.idp_name).inc()
                    
                    # Check various indicators of ID tokens
                    if header.get("typ") == "ID":
                        raise TokenTypeRejectedError("ID tokens not accepted", token_type="ID")
                    if payload.get("token_use") == "id":
                        raise TokenTypeRejectedError("ID tokens not accepted", token_type="id")
                    if "nonce" in payload:
                        raise TokenTypeRejectedError("Token appears to be ID token (has nonce)")
                except ValueError:
                    # Not a valid JWT - let the validator handle it
                    pass
            
            # Determine JWKS URL (with discovery cache support)
            jwks_url = await self._get_jwks_url()
            
            # Create or reuse validator instance
            if self._validator is None or self._validator_jwks_url != jwks_url:
                # Get audiences from IdPConfig (root level)
                expected_audiences = self.idp_config.get_audience_list()
                self._validator = LightweightValidator(
                    jwks_url=jwks_url,
                    expected_audience=expected_audiences if expected_audiences else None,
                    expected_issuer=self.expected_issuer if self.jwks_config.enforce_issuer else None,
                    expected_algorithms=self.jwks_config.expected_algs,
                    leeway=self.jwks_config.leeway_seconds,
                )
                self._validator_jwks_url = jwks_url
            
            # Validate token using new verify_jwt
            assert self._http_client is not None
            claims = await self._validator.verify_jwt(
                token,
                http=self._http_client,
            )
            
            # Record metrics
            if METRICS_AVAILABLE:
                elapsed = time.time() - start_time
                jwt_validation_seconds.labels(idp=self.idp_name, strategy='jwks').observe(elapsed)
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='success').inc()
            
            # Preserve original claims before normalization
            original_claims = dict(claims)
            
            # Normalize and return using shared function
            normalized = normalize_token_claims(
                claims,
                issuer=self.expected_issuer or "",
                validation_method="jwks",
                idp_name=self.idp_name
            )
            
            # Add raw claims as required by PDF spec
            normalized["raw"] = original_claims
            return normalized
            
        except jwt.DecodeError as e:
            # Malformed token (not valid JWT format)
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='jwks', error_type='format').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='error').inc()
            raise TokenFormatError(f"Invalid JWT format: {str(e)}")
        except jwt.ExpiredSignatureError:
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='jwks', error_type='expired').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='error').inc()
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidAudienceError:
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='jwks', error_type='audience').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='error').inc()
            raise AudienceMismatchError(
                "Token audience doesn't match",
                expected=str(self.idp_config.get_audience_list()),
                actual=None
            )
        except jwt.InvalidIssuerError:
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='jwks', error_type='issuer').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='error').inc()
            raise IssuerMismatchError(
                "Token issuer doesn't match",
                expected=self.expected_issuer,
                actual=None
            )
        except jwt.InvalidSignatureError:
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='jwks', error_type='signature').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='error').inc()
            raise SignatureValidationError("Invalid token signature")
        except ValidationError as e:
            # Our own validation errors (e.g., "Public key not found", "Invalid claims")
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='jwks', error_type='validation').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='error').inc()
            # Re-raise as-is
            raise
        except Exception as e:
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='jwks', error_type='unknown').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='jwks', result='error').inc()
            logger.error("JWKS validation failed for IdP '%s': %s", self.idp_name, e)
            raise ValidationError(f"JWKS validation failed: {str(e)}")


class IntrospectionValidator:
    """
    Validator that uses OAuth2 token introspection for validation.
    
    Wraps HardenedOAuth client with proper error handling and caching.
    """
    
    def __init__(self, idp_config: IdPConfig):
        """Initialize introspection validator with IdP configuration."""
        if not idp_config.introspection:
            raise ConfigurationError(f"Introspection config required for IdP '{idp_config.name}'")

        self.idp_config = idp_config  # Store full config for audience access
        self.idp_name = idp_config.name
        self.expected_issuer = canonicalize_issuer(idp_config.issuer)
        self.introspection_config = idp_config.introspection
        
        # Create OAuth client config with introspection URL
        from ..oauth.client import SecureOAuthConfig
        
        issuer_base = (self.expected_issuer or "").rstrip('/')
        oauth_config = SecureOAuthConfig(
            client_id=self.introspection_config.client_id,
            client_secret=self.introspection_config.client_secret or "",
            token_url=f"{issuer_base}/token",
            authorization_url=f"{issuer_base}/authorize",
            introspection_url=self.introspection_config.url,
            token_endpoint_auth_method=self.introspection_config.auth_method,
        )
        
        # Create OAuth client with proper config
        self._oauth_client = HardenedOAuth(
            config=oauth_config,
            timeout_seconds=int(self.introspection_config.timeout_seconds),
        )
        
        # Optional caching
        self._cache: Optional[LRUTTLCache] = None
        if self.introspection_config.cache_ttl_seconds > 0:
            self._cache = LRUTTLCache(
                maxsize=1000,
                default_ttl=self.introspection_config.cache_ttl_seconds
            )
        
        # HTTP client is managed internally by HardenedOAuth
        
        logger.info(
            "Initialized IntrospectionValidator for IdP '%s': url=%s, cache_ttl=%ds",
            self.idp_name,
            self.introspection_config.url,
            self.introspection_config.cache_ttl_seconds,
        )
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate token via introspection endpoint."""
        # Check cache first
        if self._cache:
            cache_key = hmac_token_key(token)
            cached_result = self._cache.get(cache_key)
            if cached_result:
                logger.debug("Introspection cache hit for IdP '%s'", self.idp_name)
                if METRICS_AVAILABLE:
                    jwt_cache_hits_total.labels(cache_type='introspection').inc()
                return cached_result
        
        try:
            # Call introspection endpoint
            start_time = time.time()
            if METRICS_AVAILABLE:
                jwt_introspection_calls_total.labels(idp=self.idp_name).inc()
            result = await self._oauth_client.introspect_token(token)
            elapsed = time.time() - start_time
            elapsed_ms = elapsed * 1000
            
            if METRICS_AVAILABLE:
                jwt_introspection_seconds.labels(idp=self.idp_name).observe(elapsed)
            
            logger.debug(
                "Introspection for IdP '%s' took %.2fms",
                self.idp_name,
                elapsed_ms
            )
            
            # Check if token is active
            if not result.get("active"):
                if METRICS_AVAILABLE:
                    jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='inactive').inc()
                    jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
                raise IntrospectionRejectedError("Token is inactive")

            # Verify issuer if present
            if "iss" in result:
                result_issuer = canonicalize_issuer(result["iss"])
                if result_issuer != self.expected_issuer:
                    if METRICS_AVAILABLE:
                        jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='issuer').inc()
                        jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
                    raise IssuerMismatchError(
                        "Token issuer doesn't match",
                        expected=self.expected_issuer,
                        actual=result_issuer
                    )

            # Check audience if configured (optional validation)
            expected_audiences = self.idp_config.get_audience_list()
            if expected_audiences:
                token_aud = result.get("aud")
                if token_aud is None:
                    if METRICS_AVAILABLE:
                        jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='audience').inc()
                        jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
                    raise AudienceMismatchError(
                        "No audience in introspection response",
                        expected=str(expected_audiences),
                        actual=None
                    )

                # Handle both string and list formats (per RFC 7662)
                token_audiences = [token_aud] if isinstance(token_aud, str) else token_aud

                # Check if any expected audience matches
                if not any(aud in expected_audiences for aud in token_audiences):
                    if METRICS_AVAILABLE:
                        jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='audience').inc()
                        jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
                    raise AudienceMismatchError(
                        "Token audience doesn't match",
                        expected=str(expected_audiences),
                        actual=str(token_audiences)
                    )
            
            # Record success metrics
            if METRICS_AVAILABLE:
                jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='success').inc()
                jwt_validation_seconds.labels(idp=self.idp_name, strategy='introspection').observe(time.time() - start_time)
            
            # Normalize claims using shared function
            # Ensure issuer is set for introspection results
            if "iss" not in result:
                result["iss"] = self.expected_issuer
            
            # Preserve original result before normalization
            original_result = dict(result)
            
            normalized = normalize_token_claims(
                result,
                issuer=result["iss"],
                validation_method="introspection",
                idp_name=self.idp_name
            )
            
            # Add raw claims as required by PDF spec
            normalized["raw"] = original_result
            
            # Cache if configured
            if self._cache:
                # Calculate TTL matching requirement: min(configured_ttl, max(30, exp - now - skew))
                ttl = self.introspection_config.cache_ttl_seconds
                if "exp" in result:
                    # Use same formula as old code with default skew of 60 seconds
                    skew = 60  # Default ttl_skew from old implementation
                    ttl = min(ttl, max(30, result["exp"] - int(time.time()) - skew))
                # else use configured_ttl as-is

                if ttl > 0:
                    cache_key = hmac_token_key(token)
                    self._cache.set(cache_key, normalized, ttl)
            
            return normalized
            
        except httpx.TimeoutException:
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='timeout').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
            raise NetworkError(
                f"Introspection timeout for IdP '{self.idp_name}'",
                operation="introspection"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                if METRICS_AVAILABLE:
                    jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='config').inc()
                    jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
                raise ConfigurationError(
                    f"Introspection authentication failed for IdP '{self.idp_name}'"
                )
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='http_error').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
            raise IntrospectionError(
                f"Introspection failed with status {e.response.status_code}",
                url=self.introspection_config.url
            )
        except ValidationError:
            # Re-raise our own errors
            raise
        except Exception as e:
            if METRICS_AVAILABLE:
                jwt_validation_errors_total.labels(idp=self.idp_name, strategy='introspection', error_type='unknown').inc()
                jwt_validation_total.labels(idp=self.idp_name, strategy='introspection', result='error').inc()
            logger.error("Introspection failed for IdP '%s': %s", self.idp_name, e)
            raise ValidationError(f"Introspection validation failed: {str(e)}")
    
    async def close(self):
        """Clean up resources."""
        if self._oauth_client:
            await self._oauth_client.aclose()


class UnifiedTokenValidator:
    """
    Router that delegates token validation to appropriate validator based on IdP configuration.

    Handles both JWT and opaque tokens, routing to JWKS or introspection validators.

    Usage Examples:
        # Manual resource management
        validator = UnifiedTokenValidator(catalogue)
        try:
            claims = await validator.validate_token(token)
        finally:
            await validator.close()

        # Preferred: Use as async context manager
        async with UnifiedTokenValidator(catalogue) as validator:
            claims = await validator.validate_token(token)
        # Resources automatically cleaned up on exit
    """
    
    def __init__(
        self,
        idp_catalogue: IdPCatalogue,
        default_idp_for_opaque: Optional[str] = None,
    ):
        """
        Initialize unified validator.

        Args:
            idp_catalogue: Catalogue of IdP configurations
            default_idp_for_opaque: Default IdP name for opaque tokens without hint

        Raises:
            ConfigurationError: If default_idp_for_opaque doesn't exist in catalogue
        """
        self.catalogue = idp_catalogue
        self.default_idp_for_opaque = default_idp_for_opaque

        # Validate default IdP exists if specified
        if default_idp_for_opaque and not idp_catalogue.for_name(default_idp_for_opaque):
            raise ConfigurationError(
                f"Default IdP for opaque tokens not found: {default_idp_for_opaque}",
                idp_name=default_idp_for_opaque
            )

        # Validators created lazily per IdP with lifecycle management
        self._validators: Dict[str, TokenValidator] = {}
        self._max_validators = 100  # Prevent unbounded growth
        self._validator_access_order: List[str] = []  # For LRU eviction

        # Shared HTTP client for introspection validators
        self._http_client: Optional[httpx.AsyncClient] = None
        self._http_client_lock = asyncio.Lock()

        # Claims mapper for normalization
        self._claims_mapper = ClaimsMapper()

        # Discovery cache (30m TTL, LRU 128 as per PDF spec)
        self._discovery_cache = LRUTTLCache(maxsize=128, default_ttl=1800)

        # Track if already closed to prevent double-close
        self._closed = False
        self._close_lock = asyncio.Lock()
        self._validators_lock = asyncio.Lock()

        logger.info(
            "Initialized UnifiedTokenValidator with %d IdPs, default_opaque=%s",
            len(idp_catalogue),
            default_idp_for_opaque,
        )
    
    async def validate_token(
        self,
        token: str,
        *,
        issuer_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route token validation to appropriate IdP and strategy.
        
        Args:
            token: Token to validate
            issuer_hint: Optional hint for opaque tokens (IdP name)
            
        Returns:
            Normalized claims dictionary with 'raw' field containing original claims
            
        Raises:
            UnknownIssuerError: No IdP configuration found
            ValidationError: Token validation failed
        """
        # Step 1: Determine IdP
        idp_config = await self._select_idp(token, issuer_hint)
        
        # Step 2: Get or create validator
        validator = await self._get_validator(idp_config)
        
        # Step 3: Validate token
        claims = await validator.validate_token(token)
        
        # Step 4: Apply claims mapping - ALWAYS run for default extraction patterns
        # ClaimsMapper has good defaults for Keycloak, Azure AD, Auth0, Cognito etc.
        # Custom mappings from config will augment these defaults if present
        mapped = self._claims_mapper.normalize(claims, idp_config)

        # Merge extracted roles and permissions into claims
        claims["roles"] = mapped.get("roles", [])
        claims["permissions"] = mapped.get("permissions", [])

        # Don't touch claims["raw"] - JWKS/Introspection validators already set it
        return claims
    
    async def _select_idp(self, token: str, issuer_hint: Optional[str]) -> IdPConfig:
        """Select IdP configuration for token validation."""
        # Try to extract issuer from JWT payload
        try:
            payload = peek_payload(token)
            issuer = payload.get("iss")
            
            if issuer:
                # Look up with prefix matching (canonicalization handled in for_issuer)
                legacy_config = self.catalogue.for_issuer(issuer)
                if legacy_config:
                    return legacy_config
                raise UnknownIssuerError(f"No IdP configuration found for issuer: {issuer}", issuer=issuer)
        except (ValueError, KeyError):
            # Token is not a valid JWT (likely opaque)
            pass
        
        # Handle opaque tokens
        if issuer_hint:
            # Look up by IdP name
            legacy_config = self.catalogue.for_name(issuer_hint)
            if legacy_config:
                return legacy_config
            raise UnknownIssuerError(f"Unknown IdP hint: {issuer_hint}")
        
        if self.default_idp_for_opaque:
            legacy_config = self.catalogue.for_name(self.default_idp_for_opaque)
            if legacy_config:
                return legacy_config
            raise ConfigurationError(
                f"Default IdP for opaque tokens not found: {self.default_idp_for_opaque}",
                idp_name=self.default_idp_for_opaque
            )
        
        raise UnknownIssuerError(
            "Cannot determine IdP for opaque token (no issuer_hint or default configured)"
        )
    
    async def _get_validator(self, idp_config: IdPConfig) -> TokenValidator:
        """Get or create validator for IdP with LRU eviction (thread-safe)."""
        if self._closed:
            raise ValidationError("UnifiedTokenValidator is closed")

        async with self._validators_lock:
            existing = self._validators.get(idp_config.name)
            if existing is None:
                # Evict least recently used if at capacity
                if len(self._validators) >= self._max_validators and self._validator_access_order:
                    lru_name = self._validator_access_order.pop(0)
                    old_validator = self._validators.pop(lru_name, None)
                    if old_validator and isinstance(old_validator, IntrospectionValidator):
                        await old_validator.close()
                    logger.info("Evicted validator for IdP '%s' (LRU)", lru_name)

                # Create new validator based on strategy
                if idp_config.strategy == ValidationStrategy.JWKS:
                    # Ensure shared HTTP client exists (separately locked)
                    async with self._http_client_lock:
                        if not self._http_client:
                            self._http_client = httpx.AsyncClient(
                                timeout=httpx.Timeout(10.0, connect=5.0)
                            )

                    validator = JWKSValidator(idp_config)
                    validator._shared_discovery_cache = self._discovery_cache
                    validator._http_client = self._http_client
                    self._validators[idp_config.name] = validator
                elif idp_config.strategy == ValidationStrategy.INTROSPECTION:
                    # No shared client is required; HardenedOAuth manages its own client
                    self._validators[idp_config.name] = IntrospectionValidator(idp_config)
                else:
                    raise ConfigurationError(
                        f"Unknown validation strategy: {idp_config.strategy}",
                        idp_name=idp_config.name
                    )

            # Update access order for LRU tracking
            if idp_config.name in self._validator_access_order:
                self._validator_access_order.remove(idp_config.name)
            self._validator_access_order.append(idp_config.name)

            return self._validators[idp_config.name]
    
    async def close(self):
        """Clean up all resources.

        This method is idempotent - calling it multiple times is safe.
        It properly closes all HTTP clients and validators.
        """
        async with self._close_lock:
            if self._closed:
                return  # Already closed

            logger.info("Closing UnifiedTokenValidator")

            # Mark as closed to prevent new operations
            self._closed = True

            # Close all validators (both JWKS and Introspection)
            errors = []
            for name, validator in list(self._validators.items()):
                try:
                    if isinstance(validator, IntrospectionValidator):
                        await validator.close()
                except Exception as e:
                    logger.error("Failed to close validator for IdP '%s': %s", name, e)
                    errors.append(e)

            # Clear validator collections
            self._validators.clear()
            self._validator_access_order.clear()

            # Close shared HTTP client
            if self._http_client:
                try:
                    await self._http_client.aclose()
                except Exception as e:
                    logger.error("Failed to close HTTP client: %s", e)
                    errors.append(e)
                finally:
                    self._http_client = None

            # Clear caches
            self._discovery_cache = LRUTTLCache(maxsize=1, default_ttl=1)  # Reset to minimal

            if errors:
                logger.warning("UnifiedTokenValidator closed with %d errors", len(errors))
            else:
                logger.info("UnifiedTokenValidator closed successfully")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.close()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor warning if not properly closed."""
        if not self._closed and self._http_client:
            logger.warning(
                "UnifiedTokenValidator not properly closed. "
                "Use 'await validator.close()' or async context manager."
            )


__all__ = [
    "TokenValidator",
    "JWKSValidator",
    "IntrospectionValidator",
    "UnifiedTokenValidator",
]