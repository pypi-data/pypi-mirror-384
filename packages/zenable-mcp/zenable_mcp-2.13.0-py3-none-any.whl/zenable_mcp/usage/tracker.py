"""Usage tracking logic for zenable_mcp commands."""

import logging
import os
from datetime import datetime, timezone
from typing import Any

import click

from zenable_mcp import __version__
from zenable_mcp.usage.fingerprint import get_system_fingerprint
from zenable_mcp.usage.models import (
    IDEOperationResult,
    ZenableMcpUsagePayload,
)
from zenable_mcp.usage.sender import send_usage_data
from zenable_mcp.utils.install_status import InstallResult

LOG = logging.getLogger(__name__)


def is_tracking_enabled() -> bool:
    """
    Check if usage tracking is enabled.

    Returns:
        True if tracking is enabled, False if disabled via environment variable
    """
    return os.environ.get("ZENABLE_DISABLE_USAGE_TRACKING", "").lower() not in (
        "1",
        "true",
        "yes",
    )


def extract_command_info(ctx: click.Context) -> tuple[str, dict[str, Any]]:
    """
    Extract command name and arguments from click context.

    Args:
        ctx: Click context from command execution

    Returns:
        Tuple of (command_string, command_args_dict)
    """
    # Build command string from context
    command_parts = []
    current_ctx = ctx

    # Walk up the context chain to build full command
    while current_ctx:
        if current_ctx.info_name:
            command_parts.insert(0, current_ctx.info_name)
        current_ctx = current_ctx.parent

    command_string = " ".join(command_parts)

    # Extract command arguments (params)
    command_args = {}
    if ctx.params:
        # Filter out None values and convert to serializable types
        for key, value in ctx.params.items():
            if value is not None:
                # Convert tuples to lists for JSON serialization
                if isinstance(value, tuple):
                    command_args[key] = list(value)
                else:
                    command_args[key] = value

    return command_string, command_args


def convert_install_results_to_operations(
    results: list[InstallResult],
) -> list[IDEOperationResult]:
    """
    Convert InstallResult objects to IDEOperationResult for tracking.

    Args:
        results: List of InstallResult objects

    Returns:
        List of IDEOperationResult objects
    """
    operations = []

    for result in results:
        # Extract IDE name from component_name (e.g., "Cursor" -> "cursor")
        ide_name = result.component_name.lower()

        # Determine operation type from status
        operation = "install"  # default
        if result.status.value == "upgraded":
            operation = "upgrade"

        # Convert status to string
        status = result.status.value

        # Determine if global based on result attributes
        is_global = getattr(result, "is_global", False)

        operations.append(
            IDEOperationResult(
                ide_name=ide_name,
                operation=operation,
                status=status,
                is_global=is_global,
                message=result.message,
            )
        )

    return operations


def track_command_usage(
    ctx: click.Context,
    results: list[InstallResult] | None = None,
    error: Exception | None = None,
    **kwargs,
) -> None:
    """
    Track usage of a zenable_mcp command.

    This is the main entry point for usage tracking. It collects
    system information, command details, and sends it to the public_api.

    Args:
        ctx: Click context from command execution
        results: Optional list of InstallResult objects from IDE operations
        error: Optional exception if command failed
        **kwargs: Additional data to include (e.g., check_stats)
    """
    # Check if tracking is disabled
    if not is_tracking_enabled():
        LOG.debug("Usage tracking disabled via environment variable")
        return

    try:
        # Get system fingerprint
        system_info, system_hash = get_system_fingerprint()

        # Extract command info
        command_string, command_args = extract_command_info(ctx)

        # Convert InstallResult objects to IDEOperationResult
        ide_operations = []
        if results:
            ide_operations = convert_install_results_to_operations(results)

        # Determine success status
        success = error is None
        if results:
            # If any result is an error, mark as not successful
            success = success and not any(r.is_error for r in results)

        # Build error message
        error_message = None
        if error:
            error_message = str(error)

        # Build payload
        payload = ZenableMcpUsagePayload(
            system_info=system_info,
            system_hash=system_hash,
            command=command_string,
            command_args=command_args,
            timestamp=datetime.now(timezone.utc),
            ide_operations=ide_operations,
            success=success,
            error_message=error_message,
            zenable_mcp_version=__version__,
        )

        # Add any additional kwargs to the payload (e.g., check_stats)
        if kwargs:
            # We'd need to extend the model to support arbitrary additional data
            # For now, just log it
            LOG.debug(f"Additional usage data: {kwargs}")

        # Send usage data (non-blocking)
        send_usage_data(payload)

    except Exception:
        # Never fail the main command due to tracking errors
        LOG.debug("Failed to track usage", exc_info=True)
