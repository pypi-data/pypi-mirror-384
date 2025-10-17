"""
Factory functions for creating token validators and FastAPI dependencies.

This module provides high-level factory functions that make it easy to
integrate token validation into services with minimal configuration.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from .config import IdPCatalogue
from .validators import UnifiedTokenValidator

logger = logging.getLogger(__name__)


def create_unified_validator(
    idps_yaml_path: str,
    default_idp_for_opaque: Optional[str] = None,
    auto_reload: bool = False,
) -> UnifiedTokenValidator:
    """
    Create a unified token validator from IdP configuration file.
    
    Args:
        idps_yaml_path: Path to YAML file containing IdP configurations
        default_idp_for_opaque: Default IdP name for opaque tokens without hint
        auto_reload: Whether to auto-reload config file on changes (for development)
        
    Returns:
        Configured UnifiedTokenValidator instance
        
    Example:
        validator = create_unified_validator(
            "ServiceConfigs/idps.yaml",
            default_idp_for_opaque="legacy",
            auto_reload=True  # For development
        )
        
        claims = await validator.validate_token(token)
    """
    # Expand environment variables in path
    expanded_path = os.path.expandvars(idps_yaml_path)
    
    # Load IdP catalogue with auto_reload support (useful for development)
    catalogue = IdPCatalogue(expanded_path, auto_reload=auto_reload)
    
    # Create unified validator
    validator = UnifiedTokenValidator(
        idp_catalogue=catalogue,
        default_idp_for_opaque=default_idp_for_opaque,
    )
    
    logger.info(
        "Created UnifiedTokenValidator from %s with %d IdPs",
        expanded_path,
        len(catalogue),
    )
    
    return validator




__all__ = [
    "create_unified_validator",
]