import logging
import secrets

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader

from broadie.config import settings

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
logger = logging.getLogger(__name__)


def check_credentials(request: Request, api_key: str | None = Security(api_key_header)) -> bool:
    """
    Validate API credentials with production-grade security.

    Security features:
    - Constant-time comparison (prevents timing attacks)
    - Null-safe client host checks
    - Audit logging for failed attempts
    - Clear error messages

    Args:
        request: FastAPI request object
        api_key: Authorization header value

    Returns:
        bool: True if authentication succeeds

    Raises:
        HTTPException: 403 if authentication fails
    """
    client_host = request.client.host if request.client else None

    # API key validation
    if not api_key or not api_key.startswith("Bearer "):
        logger.warning(
            "Missing or malformed Authorization header from %s",
            client_host or "unknown",
        )
        raise HTTPException(
            status_code=403,
            detail="Missing or malformed Authorization header. Use 'Authorization: Bearer <key>'",
        )

    token = api_key.removeprefix("Bearer ").strip()
    if not token:
        logger.warning("Empty API key from %s", client_host or "unknown")
        raise HTTPException(status_code=403, detail="Empty API key")

    # No API keys configured - fail closed for security
    if not settings.API_KEYS:
        logger.error(
            "Authentication attempted but no API keys configured (from %s)",
            client_host or "unknown",
        )
        raise HTTPException(
            status_code=403,
            detail="API authentication is not configured on this server",
        )

    # Constant-time comparison to prevent timing attacks
    if any(secrets.compare_digest(token, valid_key) for valid_key in settings.API_KEYS):
        logger.debug("Successful authentication from %s", client_host or "unknown")
        return True

    logger.warning(
        "Invalid API key attempt from %s (key prefix: %s...)",
        client_host or "unknown",
        token[:8] if len(token) >= 8 else "too_short",
    )
    raise HTTPException(status_code=403, detail="Invalid API key")
