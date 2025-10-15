"""Data models for usage tracking."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SystemInfo(BaseModel):
    """High-level system information for grouping."""

    model_config = ConfigDict(strict=True)

    os_type: str  # e.g., "Linux", "Darwin", "Windows"
    platform: str  # e.g., "linux", "darwin", "win32"
    architecture: str  # e.g., "x86_64", "arm64"
    python_version: str  # e.g., "3.11.5"


class IDEOperationResult(BaseModel):
    """Result of an IDE operation (install/upgrade/etc.)."""

    model_config = ConfigDict(strict=True)

    ide_name: str  # e.g., "cursor", "claude-code", "vscode"
    operation: str  # e.g., "install", "upgrade"
    status: str  # e.g., "success", "failed", "already_installed", "skipped"
    is_global: bool  # whether --global flag was used
    message: str | None = None


class ZenableMcpUsagePayload(BaseModel):
    """Usage data to send to public_api."""

    model_config = ConfigDict(strict=True)

    integration: str = "zenable_mcp"  # always this value
    system_info: SystemInfo  # high-level system info
    system_hash: str  # SHA256 hash of system_info for grouping
    command: str  # e.g., "install mcp", "install hook", "check"
    command_args: dict  # parsed args/flags from click context
    timestamp: datetime
    ide_operations: list[IDEOperationResult] = []
    # Additional contextual info
    success: bool  # overall command success
    error_message: str | None = None
    # Version info
    zenable_mcp_version: str
    payload_version: str = "1.0"
