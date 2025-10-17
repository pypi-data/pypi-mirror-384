"""
Typed error hierarchy for token validation.

This module provides a structured exception hierarchy for token validation failures,
with clear semantics and a stage field to identify where validation failed.
"""

from typing import Optional


class ValidationError(Exception):
    """Base exception for all token validation errors."""
    
    def __init__(self, message: str, stage: Optional[str] = None):
        super().__init__(message)
        self.stage = stage  # e.g., "routing", "jwks", "introspection", "normalization"


class UnknownIssuerError(ValidationError):
    """Token issuer is not configured in any IdP."""
    
    def __init__(self, message: str, issuer: Optional[str] = None):
        super().__init__(message, stage="routing")
        self.issuer = issuer


class TokenFormatError(ValidationError):
    """Token is not a valid JWT or doesn't meet format requirements."""
    
    def __init__(self, message: str):
        super().__init__(message, stage="parsing")


class TokenTypeRejectedError(ValidationError):
    """Token type is not accepted (e.g., ID token when accept_id_tokens=False)."""
    
    def __init__(self, message: str, token_type: Optional[str] = None):
        super().__init__(message, stage="validation")
        self.token_type = token_type


class SignatureValidationError(ValidationError):
    """JWT signature validation failed."""
    
    def __init__(self, message: str):
        super().__init__(message, stage="jwks")


class AudienceMismatchError(ValidationError):
    """Token audience doesn't match expected value."""
    
    def __init__(self, message: str, expected: Optional[str] = None, actual: Optional[str] = None):
        super().__init__(message, stage="validation")
        self.expected = expected
        self.actual = actual


class IssuerMismatchError(ValidationError):
    """Token issuer doesn't match expected value."""
    
    def __init__(self, message: str, expected: Optional[str] = None, actual: Optional[str] = None):
        super().__init__(message, stage="validation")
        self.expected = expected
        self.actual = actual


class TokenExpiredError(ValidationError):
    """Token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, stage="validation")


class IntrospectionRejectedError(ValidationError):
    """Introspection endpoint reported token as inactive."""
    
    def __init__(self, message: str = "Token is inactive"):
        super().__init__(message, stage="introspection")


class DiscoveryError(ValidationError):
    """OIDC discovery failed."""
    
    def __init__(self, message: str):
        super().__init__(message, stage="discovery")


class JWKSFetchError(ValidationError):
    """Failed to fetch JWKS from endpoint."""
    
    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message, stage="jwks")
        self.url = url


class IntrospectionError(ValidationError):
    """Introspection endpoint call failed."""
    
    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message, stage="introspection")
        self.url = url


class NetworkError(ValidationError):
    """Network error during validation (timeout, connection error, etc.)."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, stage="network")
        self.operation = operation


class ConfigurationError(ValidationError):
    """IdP configuration is invalid or incomplete."""
    
    def __init__(self, message: str, idp_name: Optional[str] = None):
        super().__init__(message, stage="configuration")
        self.idp_name = idp_name


class EnrichmentUnavailableError(ValidationError):
    """Claims enrichment failed but validation succeeded."""
    
    def __init__(self, message: str):
        super().__init__(message, stage="enrichment")


__all__ = [
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
]