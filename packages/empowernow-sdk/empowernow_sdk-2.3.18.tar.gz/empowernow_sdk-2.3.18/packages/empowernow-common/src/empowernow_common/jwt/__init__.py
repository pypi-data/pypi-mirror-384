"""
JWT validation module for EmpowerNow services.

This module provides unified token validation supporting multiple IdPs
with both JWKS and introspection validation strategies.
"""

# Core validators
from .validators import (
    TokenValidator,
    JWKSValidator,
    IntrospectionValidator,
    UnifiedTokenValidator,
)

# Factory functions
from .factory import (
    create_unified_validator,
)

# Configuration
from .config import (
    ValidationStrategy,
    JWKSConfig,
    IntrospectionConfig,
    IdPConfig,
    IdPCatalogue,
)

# Errors
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
    DiscoveryError,
    JWKSFetchError,
    IntrospectionError,
    NetworkError,
    ConfigurationError,
    EnrichmentUnavailableError,
)

# Utilities
from .utils import (
    peek_header,
    peek_payload,
    peek_header_and_payload,
    canonicalize_issuer,
    hmac_token_key,
    LRUTTLCache,
)

# Legacy exports for backwards compatibility
from .lightweight_validator import LightweightValidator, create_validator

__all__ = [
    # Validators
    "TokenValidator",
    "JWKSValidator",
    "IntrospectionValidator",
    "UnifiedTokenValidator",
    # Factory
    "create_unified_validator",
    # Config
    "ValidationStrategy",
    "JWKSConfig",
    "IntrospectionConfig", 
    "IdPConfig",
    "IdPCatalogue",
    # Errors
    "ValidationError",
    "UnknownIssuerError",
    "TokenFormatError",
    "TokenTypeRejectedError",
    "SignatureValidationError",
    "AudienceMismatchError",
    "IssuerMismatchError",
    "TokenExpiredError",
    "IntrospectionRejectedError",
    "DiscoveryError",
    "JWKSFetchError",
    "IntrospectionError",
    "NetworkError",
    "ConfigurationError",
    "EnrichmentUnavailableError",
    # Utils
    "peek_header",
    "peek_payload",
    "peek_header_and_payload",
    "canonicalize_issuer",
    "hmac_token_key",
    "LRUTTLCache",
    # Legacy
    "LightweightValidator",
    "create_validator",
]
