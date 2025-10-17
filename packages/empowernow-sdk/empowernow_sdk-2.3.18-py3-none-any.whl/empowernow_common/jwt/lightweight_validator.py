"""
Lightweight JWT Validator shared across services per BFF Authentication Architecture P1-5.

Features:
- Validate JWT signature using JWKS
- Check token expiration
- Validate audience
- Minimal deps and fast
- Optional FIPS/HardenedOAuth JWKS fetch when empowernow_common.oauth is available

Public API:
- ValidationError (exception)
- class LightweightValidator
- create_validator(jwks_url: str | None = None, expected_audience: str | list[str] | None = None)
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, UTC
import os
import time
import logging

import jwt
from cachetools import TTLCache

logger = logging.getLogger("empowernow_common.jwt.lightweight_validator")


class ValidationError(Exception):
    pass


class LightweightValidator:
    def __init__(
        self,
        jwks_url: str,
        expected_audience: str | List[str] | None = None,
        expected_issuer: str | None = None,
        expected_algorithms: List[str] | None = None,
        leeway: int = 60,
        cache_ttl: int = 1800,
        timeout: float = 5.0,
        use_hardened_oauth: bool = False,
    ):
        self.jwks_url = jwks_url
        self.expected_audience = expected_audience
        self.expected_issuer = expected_issuer
        self.expected_algorithms = expected_algorithms or ["RS256", "PS256", "ES256"]
        self.leeway = leeway
        self.timeout = timeout
        self.use_hardened_oauth = use_hardened_oauth
        self._jwks_cache: TTLCache[str, Dict[str, Any]] = TTLCache(maxsize=1, ttl=cache_ttl)
        self._validation_count = 0
        self._validation_errors = 0
        self._cache_hits = 0

        logger.info(
            "Initialized LightweightValidator: jwks_url=%s, audience=%s, issuer=%s, algorithms=%s, leeway=%ds, cache_ttl=%ds, hardened_oauth=%s",
            jwks_url,
            expected_audience,
            expected_issuer,
            expected_algorithms,
            leeway,
            cache_ttl,
            use_hardened_oauth,
        )

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Original validation method for backward compatibility."""
        start = time.time()
        self._validation_count += 1
        try:
            if not token or not isinstance(token, str):
                return None

            # Create HTTP client per-call for backward compatibility
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                claims = await self.verify_jwt(token, http=client)
                return claims
        except Exception as e:
            self._validation_errors += 1
            logger.debug("Token validation failed: %s", e)
            return None

    async def verify_jwt(
        self,
        token: str,
        *,
        issuer: str | None = None,
        audience: List[str] | str | None = None,
        leeway: int | None = None,
        expected_algs: List[str] | None = None,
        jwks_url_override: str | None = None,
        http: httpx.AsyncClient,
    ) -> Dict[str, Any]:
        """
        Verify JWT token with explicit parameters.
        
        This method allows overriding instance-level configuration for specific validations.
        Raises exceptions on validation failures per PDF spec.
        """
        # Use provided values or fall back to instance defaults
        expected_issuer = issuer if issuer is not None else self.expected_issuer
        expected_audience = audience if audience is not None else self.expected_audience
        expected_leeway = leeway if leeway is not None else self.leeway
        expected_algorithms = expected_algs if expected_algs is not None else self.expected_algorithms
        jwks_url_to_use = jwks_url_override if jwks_url_override else self.jwks_url
        
        # Start validation
        start = time.time()
        try:
            if not token or not isinstance(token, str):
                raise ValidationError("Token must be a non-empty string")

            try:
                unverified_header = jwt.get_unverified_header(token)
                key_id = unverified_header.get("kid")
                algorithm = unverified_header.get("alg")
            except jwt.DecodeError:
                # Bubble up format errors so outer layers can map to TokenFormatError
                raise

            try:
                # Get public key using instance cache and provided HTTP client
                public_key = await self._get_public_key(
                    key_id, jwks_url_to_use, algorithm,
                    http_client=http
                )
                if not public_key:
                    logger.debug("Public key not found for kid: %s", key_id)
                    raise ValidationError(f"Public key not found for kid: {key_id}")
            except ValidationError:
                raise
            except Exception as e:
                logger.error("Failed to get public key: %s", e)
                raise ValidationError(f"Public key retrieval failed: {e}")

            try:
                # Build decode kwargs with local parameters
                decode_kwargs = {
                    "key": public_key,
                    "algorithms": expected_algorithms,
                    "options": {
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_aud": expected_audience is not None,
                        "verify_iss": expected_issuer is not None,
                    },
                    "leeway": expected_leeway,
                }
                
                # Add audience if configured
                if expected_audience is not None:
                    decode_kwargs["audience"] = expected_audience
                
                # Add issuer if configured
                if expected_issuer is not None:
                    decode_kwargs["issuer"] = expected_issuer
                
                claims = jwt.decode(token, **decode_kwargs)

                if not self._validate_claims(claims):
                    raise ValidationError("Invalid claims in token")

                logger.debug(
                    "Token validation successful: sub=%s, time_ms=%.2f",
                    claims.get("sub", "unknown"),
                    (time.time() - start) * 1000,
                )
                return claims
            except jwt.ExpiredSignatureError:
                # Bubble up so outer validator can map to TokenExpiredError
                raise
            except jwt.InvalidAudienceError:
                # Bubble up so outer validator can map to AudienceMismatchError
                raise
            except jwt.InvalidIssuerError:
                # Bubble up so outer validator can map to IssuerMismatchError
                raise
            except jwt.InvalidSignatureError:
                # Bubble up so outer validator can map to SignatureValidationError
                raise
            except jwt.InvalidTokenError as e:
                logger.debug("Invalid token: %s", e)
                # Keep generic invalid token as our ValidationError; outer will treat as generic failure
                raise ValidationError(f"Invalid token: {e}")
        except ValidationError:
            raise
        except Exception as e:
            logger.error("Unexpected validation error: %s", e)
            raise ValidationError(f"Token validation failed: {e}")
    
    async def _get_public_key(
        self,
        key_id: str | None,
        jwks_url: str,
        algorithm: str | None,
        http_client: httpx.AsyncClient,
    ) -> str:
        """Get public key from JWKS endpoint."""
        try:
            # Check instance cache with URL-specific key
            cache_key = f"jwks:{jwks_url}"
            
            # Try to get from instance cache
            jwks_data = self._jwks_cache.get(cache_key)
            if jwks_data:
                self._cache_hits += 1
            else:
                jwks_data = await self._fetch_jwks(jwks_url, http_client=http_client)
                if jwks_data:
                    # Store in instance cache
                    self._jwks_cache[cache_key] = jwks_data

            if not jwks_data:
                raise ValidationError(f"Failed to fetch JWKS from {jwks_url}")

            keys = jwks_data.get("keys", [])
            
            # If we have a key_id, try to find it
            if key_id:
                for key in keys:
                    if key.get("kid") == key_id:
                        return self._jwk_to_pem(key)
                logger.debug("kid not found in JWKS: %s", key_id)
                raise ValidationError(f"Key ID '{key_id}' not found in JWKS")
            
            # No kid in token header - strict single candidate matching
            # This is important for some IdPs that don't use kid
            if algorithm:
                matching_keys = []
                for key in keys:
                    key_alg = key.get("alg")
                    # Match if algorithm explicitly matches or if no alg specified and kty matches
                    if key_alg == algorithm:
                        matching_keys.append(key)
                    elif not key_alg and key.get("kty") == "RSA" and algorithm.startswith("RS"):
                        matching_keys.append(key)
                    elif not key_alg and key.get("kty") == "EC" and algorithm.startswith("ES"):
                        matching_keys.append(key)

                if len(matching_keys) == 1:
                    # Exactly one match - use it
                    return self._jwk_to_pem(matching_keys[0])
                elif len(matching_keys) > 1:
                    # Multiple matches - ambiguous
                    raise ValidationError(f"Multiple keys match algorithm '{algorithm}' - cannot determine correct key without kid")
                else:
                    # No matches
                    raise ValidationError(f"No keys match algorithm '{algorithm}'")
            else:
                # No algorithm in token header either
                raise ValidationError("Token missing both kid and alg - cannot select key from JWKS")
        except ValidationError:
            raise
        except Exception as e:
            logger.error("Failed to get public key for kid %s: %s", key_id, e)
            raise ValidationError(f"Failed to get public key: {e}")

    async def _fetch_jwks(self, jwks_url: str, http_client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        """Fetch JWKS from endpoint using provided HTTP client."""
        try:
            # Use provided HTTP client directly
            resp = await http_client.get(jwks_url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed to fetch JWKS from %s: %s", jwks_url, e)
            return None

    def _jwk_to_pem(self, jwk: Dict[str, Any]) -> str:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa, ec
            import base64

            kty = jwk.get("kty")
            if kty == "RSA":
                n = base64.urlsafe_b64decode(self._add_padding(jwk["n"]))
                e = base64.urlsafe_b64decode(self._add_padding(jwk["e"]))
                n_int = int.from_bytes(n, byteorder="big")
                e_int = int.from_bytes(e, byteorder="big")
                public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
            elif kty == "EC":
                x = base64.urlsafe_b64decode(self._add_padding(jwk["x"]))
                y = base64.urlsafe_b64decode(self._add_padding(jwk["y"]))
                crv = jwk.get("crv")
                curves = {
                    "P-256": ec.SECP256R1(),
                    "P-384": ec.SECP384R1(),
                    "P-521": ec.SECP521R1(),
                }
                curve = curves.get(crv)
                if not curve:
                    raise ValidationError(f"Unsupported EC curve: {crv}")
                public_key = ec.EllipticCurvePublicNumbers(
                    int.from_bytes(x, byteorder="big"),
                    int.from_bytes(y, byteorder="big"),
                    curve,
                ).public_key()
            else:
                raise ValidationError(f"Unsupported JWK kty: {kty}")

            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return pem.decode("utf-8")
        except Exception as e:
            logger.error("Failed to convert JWK to PEM: %s", e)
            raise ValidationError(f"Key conversion failed: {e}")

    def _add_padding(self, b64: str) -> str:
        missing = len(b64) % 4
        if missing:
            b64 += "=" * (4 - missing)
        return b64

    def _validate_claims(self, claims: Dict[str, Any]) -> bool:
        if not claims.get("sub"):
            logger.debug("Missing subject claim")
            return False
        # IAT claim is optional - only validate if present
        iat = claims.get("iat")
        if iat is not None:
            try:
                if isinstance(iat, (int, float)):
                    now = datetime.now(UTC).timestamp()
                    if iat > now + 300:
                        logger.debug("Token issued in the future beyond skew")
                        return False
            except Exception:
                logger.debug("Invalid iat claim type")
                return False
        return True

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "validation_count": self._validation_count,
            "validation_errors": self._validation_errors,
            "cache_hits": self._cache_hits,
            "error_rate": (self._validation_errors / self._validation_count) if self._validation_count else 0.0,
            "cache_hit_rate": (self._cache_hits / self._validation_count) if self._validation_count else 0.0,
        }


def create_validator(
    jwks_url: str | None = None,
    expected_audience: str | List[str] | None = None,
    *,
    use_hardened_oauth: bool | None = None,
) -> LightweightValidator:
    """Factory with sensible defaults and env overrides.

    Env support:
      - OIDC_JWKS_URL
      - OIDC_EXPECTED_AUD (comma-separated to allow multiple)
      - EMPOWERNOW_FIPS_ENABLE (when set to true, enable HardenedOAuth)
    """
    resolved_jwks = os.getenv("OIDC_JWKS_URL") or jwks_url or "http://idp-app:8002/api/oidc/jwks"

    aud_env = os.getenv("OIDC_EXPECTED_AUD")
    if aud_env:
        aud_values = [a.strip() for a in aud_env.split(",") if a.strip()]
        resolved_aud: str | List[str] = aud_values if len(aud_values) > 1 else aud_values[0]
    else:
        resolved_aud = expected_audience or "empowernow"

    if use_hardened_oauth is None:
        # Default: FIPS OFF. Opt-in when EMPOWERNOW_FIPS_ENABLE=true
        use_hardened_oauth = os.getenv("EMPOWERNOW_FIPS_ENABLE", "").lower() in ("1", "true", "yes")

    return LightweightValidator(
        jwks_url=resolved_jwks,
        expected_audience=resolved_aud,
        use_hardened_oauth=use_hardened_oauth,
    )


