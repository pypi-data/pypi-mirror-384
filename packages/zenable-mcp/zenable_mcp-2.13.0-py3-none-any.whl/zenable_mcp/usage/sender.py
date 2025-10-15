"""HTTP client for sending usage data to public_api."""

import json
import logging
import os
from http.client import HTTPException

import requests

from zenable_mcp.usage.models import ZenableMcpUsagePayload

LOG = logging.getLogger(__name__)

# Public API endpoint (configurable via environment variable)
PUBLIC_API_URL = os.environ.get(
    "ZENABLE_PUBLIC_API_URL", "https://www.zenable.app/api/public/usage"
)

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 5


def send_usage_data(payload: ZenableMcpUsagePayload) -> None:
    """
    Send usage data to public_api endpoint.

    This function is non-blocking and will not raise exceptions.
    All failures are logged but don't affect the main command.

    Args:
        payload: ZenableMcpUsagePayload to send
    """
    try:
        # Serialize payload to JSON
        request_body = {
            "integration": payload.integration,
            "system_hash": payload.system_hash,
            "usage_data": {
                "system_info": payload.system_info.model_dump(),
                "command": payload.command,
                "command_args": payload.command_args,
                "timestamp": payload.timestamp.isoformat(),
                "ide_operations": [op.model_dump() for op in payload.ide_operations],
                "success": payload.success,
                "error_message": payload.error_message,
                "zenable_mcp_version": payload.zenable_mcp_version,
                "payload_version": payload.payload_version,
            },
        }

        # Send POST request (no authentication)
        response = requests.post(
            PUBLIC_API_URL,
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )

        # Log response
        if response.status_code == 200:
            LOG.debug("Usage data sent successfully")
        else:
            LOG.debug(
                f"Usage tracking failed: HTTP {response.status_code} - {response.text}"
            )

    except requests.exceptions.Timeout:
        LOG.debug("Usage tracking timeout - request took too long")
    except requests.exceptions.ConnectionError:
        LOG.debug("Usage tracking failed - connection error")
    except HTTPException:
        LOG.debug("Usage tracking failed - HTTP error", exc_info=True)
    except json.JSONDecodeError:
        LOG.debug("Usage tracking failed - JSON encoding error", exc_info=True)
    except Exception:
        # Catch all other exceptions to ensure we never break the main command
        LOG.debug("Usage tracking failed unexpectedly", exc_info=True)
