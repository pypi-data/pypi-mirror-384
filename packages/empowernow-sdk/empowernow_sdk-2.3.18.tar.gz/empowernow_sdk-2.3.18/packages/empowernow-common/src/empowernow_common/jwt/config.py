"""
Configuration dataclasses for token validation.

This module provides structured configuration for different validation strategies,
including IdP catalogue management for multi-tenant services.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Literal, Union
from enum import Enum

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover – optional dep
    yaml = None  # type: ignore


class ValidationStrategy(str, Enum):
    """Token validation strategy for an IdP."""
    JWKS = "JWKS"
    INTROSPECTION = "INTROSPECTION"


@dataclass(slots=True)
class JWKSConfig:
    """Configuration for JWKS-based token validation."""

    jwks_url_override: Optional[str] = None
    enforce_issuer: bool = True
    leeway_seconds: int = 60
    accept_id_tokens: bool = False
    expected_algs: List[str] = field(default_factory=lambda: ["RS256", "ES256"])
    
    def __post_init__(self):
        """Validate JWKS configuration."""
        if self.leeway_seconds < 0:
            raise ValueError("leeway_seconds must be non-negative")
        if not self.expected_algs:
            raise ValueError("expected_algs must contain at least one algorithm")


@dataclass(slots=True)
class IntrospectionConfig:
    """Configuration for introspection-based token validation."""
    
    url: str
    client_id: str
    client_secret: Optional[str] = None
    auth_method: Literal["client_secret_basic", "client_secret_post", "private_key_jwt"] = "client_secret_basic"
    cache_ttl_seconds: int = 0  # Default: no caching
    timeout_seconds: float = 5.0
    
    def __post_init__(self):
        """Validate introspection configuration."""
        if not self.url:
            raise ValueError("Introspection URL is required")
        if not self.client_id:
            raise ValueError("Client ID is required for introspection")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.auth_method in ["client_secret_basic", "client_secret_post"] and not self.client_secret:
            raise ValueError(f"client_secret required for auth_method={self.auth_method}")


@dataclass(slots=True)
class IdPConfig:
    """Enhanced IdP configuration supporting both validation strategies."""

    name: str
    issuer: str

    # Strategy selection
    strategy: ValidationStrategy = ValidationStrategy.JWKS

    # Root-level audience configuration (optional)
    # Can be a single string or list of strings
    audience: Optional[Union[str, List[str]]] = None

    # Strategy-specific configs
    jwks: Optional[JWKSConfig] = None
    introspection: Optional[IntrospectionConfig] = None

    # Claims processing
    claims_mapping: Optional[Dict[str, Any]] = None

    # Optional stricter behavior
    accept_id_tokens: bool = False
    
    def __post_init__(self):
        """Validate IdP configuration consistency."""
        if not self.name:
            raise ValueError("IdP name is required")
        if not self.issuer:
            raise ValueError("IdP issuer is required")

        # Ensure appropriate config exists for chosen strategy
        if self.strategy == ValidationStrategy.JWKS and not self.jwks:
            # Create default JWKS config
            self.jwks = JWKSConfig()
        elif self.strategy == ValidationStrategy.INTROSPECTION and not self.introspection:
            raise ValueError(f"IdP '{self.name}' strategy is INTROSPECTION but no introspection config provided")

    def get_audience_list(self) -> List[str]:
        """Normalize audience to list format."""
        if not self.audience:
            return []
        if isinstance(self.audience, str):
            return [self.audience]
        return self.audience
    
    @classmethod
    def from_legacy(cls, config: Dict[str, Any]) -> "IdPConfig":
        """
        Create IdPConfig from either modern or legacy configuration format.

        Modern format: Has nested jwks/introspection sections or explicit strategy
        Legacy format: Flat structure with introspection_url at top level
        """
        # Modern format detection - has strategy or nested structures
        if "strategy" in config or "jwks" in config or "introspection" in config:
            # Modern format - convert nested dicts to config objects
            jwks = JWKSConfig(**config["jwks"]) if config.get("jwks") else None
            introspection = IntrospectionConfig(**config["introspection"]) if config.get("introspection") else None

            return cls(
                name=config["name"],
                issuer=config["issuer"],
                strategy=ValidationStrategy(config.get("strategy", "JWKS")),
                audience=config.get("audience"),  # Root-level audience
                jwks=jwks,
                introspection=introspection,
                claims_mapping=config.get("claims_mapping"),
                accept_id_tokens=config.get("accept_id_tokens", False),
            )

        # Legacy format - determine strategy based on available fields
        if config.get("introspection_url"):
            # Legacy introspection config - default to INTROSPECTION with JWKS fallback
            strategy = ValidationStrategy.INTROSPECTION
            introspection = IntrospectionConfig(
                url=config["introspection_url"],
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                cache_ttl_seconds=config.get("cache_ttl_seconds", 0),
                timeout_seconds=config.get("timeout_seconds", 5.0),
            )

            # Create JWKS config as fallback if jwks_url exists
            jwks = None
            if config.get("jwks_url"):
                jwks = JWKSConfig(
                    jwks_url_override=config.get("jwks_url"),
                    enforce_issuer=config.get("enforce_issuer", True),
                    leeway_seconds=config.get("leeway_seconds", 60),
                    accept_id_tokens=config.get("accept_id_tokens", False),
                    expected_algs=config.get("expected_algs", ["RS256", "ES256"]),
                )
        else:
            # Legacy JWKS-only config (no introspection_url)
            strategy = ValidationStrategy.JWKS
            introspection = None

            jwks = JWKSConfig(
                jwks_url_override=config.get("jwks_url"),
                enforce_issuer=config.get("enforce_issuer", True),
                leeway_seconds=config.get("leeway_seconds", 60),
                accept_id_tokens=config.get("accept_id_tokens", False),
                expected_algs=config.get("expected_algs", ["RS256", "ES256"]),
            )

        return cls(
            name=config["name"],
            issuer=config["issuer"],
            strategy=strategy,
            audience=config.get("audience"),  # Root-level audience (legacy format)
            introspection=introspection,
            jwks=jwks,
            claims_mapping=config.get("claims_mapping"),
            accept_id_tokens=config.get("accept_id_tokens", False),
        )


class IdPCatalogue:
    """Load & query an IdP YAML catalogue.

    Parameters
    ----------
    path:
        Path to the YAML file.  Environment variables inside the path are
        expanded (e.g. ``"$HOME/idps.yaml"``).
    auto_reload:
        If *True*, the file's *mtime* is checked on every lookup and the file
        is re-loaded automatically when it changes.  Cheap `stat()` call; safe
        for hot-reload in dev containers.
    """

    def __init__(self, path: str | Path, *, auto_reload: bool = False):
        self._path = Path(os.path.expandvars(path)).expanduser().resolve()
        self._auto_reload = auto_reload
        self._idps: List[IdPConfig] = []
        self._mtime = 0.0

        self._load()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def for_issuer(self, issuer: str) -> Optional[IdPConfig]:
        """Return the IdP whose ``issuer`` is the longest prefix of *issuer* (after canonicalization)."""

        if self._auto_reload:
            self._maybe_reload()

        # Canonicalize the issuer (strip trailing slash)
        normalized_issuer = self._canonicalize_issuer(issuer)
        
        best: Optional[IdPConfig] = None
        for idp in self._idps:
            normalized_idp_issuer = self._canonicalize_issuer(idp.issuer)
            if normalized_issuer.startswith(normalized_idp_issuer) and (
                best is None or len(normalized_idp_issuer) > len(self._canonicalize_issuer(best.issuer))
            ):
                best = idp
        return best
    
    def for_name(self, name: str) -> Optional[IdPConfig]:
        """Return the IdP with the given name."""
        
        if self._auto_reload:
            self._maybe_reload()
        
        for idp in self._idps:
            if idp.name == name:
                return idp
        return None
    
    def _canonicalize_issuer(self, issuer: str) -> str:
        """Canonicalize issuer URL by stripping trailing slash."""
        if issuer:
            return issuer.rstrip('/')
        return issuer

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _maybe_reload(self) -> None:
        try:
            m = self._path.stat().st_mtime
            if m != self._mtime:
                self._load()
        except FileNotFoundError:
            # Catalogue deleted – keep old copy
            pass

    def _load(self) -> None:
        if yaml is None:
            raise ImportError("PyYAML required: pip install pyyaml")

        raw = yaml.safe_load(self._path.read_text("utf-8")) or {}
        entries = raw.get("idps", [])
        # Use from_legacy to convert old YAML format to enhanced IdPConfig
        self._idps = [IdPConfig.from_legacy(entry) for entry in entries]
        self._mtime = self._path.stat().st_mtime

    # Convenience len / iter implementation
    def __len__(self) -> int:  # noqa: D401 – simple wrapper
        return len(self._idps)

    def __iter__(self):  # noqa: D401
        return iter(self._idps)


__all__ = [
    "ValidationStrategy",
    "JWKSConfig",
    "IntrospectionConfig",
    "IdPConfig",
    "IdPCatalogue",
]