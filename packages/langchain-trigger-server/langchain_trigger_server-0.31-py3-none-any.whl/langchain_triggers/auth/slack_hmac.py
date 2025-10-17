"""Slack HMAC signature verification for webhook authentication.

Slack uses HMAC-SHA256 signatures to verify webhook authenticity.
Each request includes an X-Slack-Signature header that must be verified
against your app's signing secret.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time

logger = logging.getLogger(__name__)


class SlackSignatureVerificationError(Exception):
    """Exception raised when Slack signature verification fails."""

    pass


def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    body: str,
    signature: str,
    max_age_seconds: int = 300,
) -> bool:
    try:
        # Verify timestamp to prevent replay attacks
        current_time = int(time.time())
        request_time = int(timestamp)

        if abs(current_time - request_time) > max_age_seconds:
            logger.error(
                f"Slack request timestamp too old. "
                f"Current: {current_time}, Request: {request_time}, "
                f"Diff: {abs(current_time - request_time)}s"
            )
            raise SlackSignatureVerificationError(
                f"Request timestamp is too old (>{max_age_seconds}s). Possible replay attack."
            )

        # Format: v0:{timestamp}:{body}
        sig_basestring = f"v0:{timestamp}:{body}"

        # Create HMAC-SHA256 hash
        my_signature = (
            "v0="
            + hmac.new(
                signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
            ).hexdigest()
        )

        if not hmac.compare_digest(my_signature, signature):
            logger.error(
                f"Slack signature mismatch. Expected: {my_signature}, Got: {signature}"
            )
            raise SlackSignatureVerificationError("Signature verification failed")

        logger.info("Successfully verified Slack webhook signature")
        return True

    except ValueError as e:
        logger.error(f"Invalid timestamp format: {e}")
        raise SlackSignatureVerificationError(f"Invalid timestamp: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during Slack signature verification: {e}")
        raise SlackSignatureVerificationError(f"Verification error: {str(e)}")


def get_slack_signing_secret() -> str | None:
    """Get Slack signing secret from SLACK_SIGNING_SECRET environment variable."""
    secret = os.getenv("SLACK_SIGNING_SECRET")
    if not secret:
        logger.warning("SLACK_SIGNING_SECRET environment variable not set")
    return secret


def extract_slack_headers(headers: dict) -> tuple[str | None, str | None]:
    """Extract Slack signature and timestamp from request headers."""
    signature = headers.get("x-slack-signature") or headers.get("X-Slack-Signature")
    timestamp = headers.get("x-slack-request-timestamp") or headers.get(
        "X-Slack-Request-Timestamp"
    )

    return signature, timestamp
