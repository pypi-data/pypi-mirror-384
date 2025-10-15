"""MCP client for communicating with the Zenable MCP server."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import click
import git
import httpx
from fastmcp import Client as FastMCPClient
from fastmcp.client.auth import OAuth
from fastmcp.client.transports import StreamableHttpTransport

from zenable_mcp.exceptions import APIError
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.utils.retries import is_transient_error, retry_on_error

# Suppress noisy MCP library error logs that show full stack traces to users
# These errors are already handled by our retry logic with user-friendly messages
# The "mcp" logger produces "[ERROR] Error reading SSE stream" with full tracebacks
logging.getLogger("mcp").setLevel(logging.CRITICAL)


class ZenableMCPClient:
    """Client for communicating with the Zenable MCP server."""

    def __init__(
        self, base_url: Optional[str] = None, token_cache_dir: Optional[Path] = None
    ):
        """
        Initialize the Zenable MCP client with OAuth authentication.

        Args:
            base_url: Optional base URL for the MCP server
            token_cache_dir: Directory to cache OAuth tokens
        """
        # Get base URL from parameter, env var, or default
        self.base_url = (
            base_url
            or os.environ.get("ZENABLE_MCP_ENDPOINT")
            or "https://mcp.zenable.app"
        ).rstrip("/")  # Remove trailing slash for consistency

        # Use persistent cache directory
        self.token_cache_dir = (
            token_cache_dir or Path.home() / ".zenable" / "oauth-mcp-client-cache"
        )
        self.token_cache_dir.mkdir(parents=True, exist_ok=True)

        # Create OAuth instance - let FastMCP handle everything
        self.oauth = OAuth(
            mcp_url=self.base_url,
            scopes=["openid", "profile", "email"],
            client_name="Zenable MCP Client",
            token_storage_cache_dir=self.token_cache_dir,
            callback_port=23014,  # Fixed port for consistency
        )

        self.client = None

    async def __aenter__(self):
        """Enter async context manager."""
        echo(f"Connecting to MCP server at {self.base_url}", persona=Persona.POWER_USER)

        # Use StreamableHttpTransport with SSE read timeout
        # Per FastMCP/MCP SDK research and production requirements:
        # - Conformance checks normally complete in <10 seconds
        # - 90 seconds provides buffer for OAuth, slow networks, edge cases
        # - Combined with 3x retry for transient failures
        transport = StreamableHttpTransport(
            self.base_url,
            sse_read_timeout=90.0,  # 90 second timeout for SSE streaming
        )

        # Initialize client with OAuth and timeouts
        # - init_timeout: Covers OAuth flow + connection establishment
        # - timeout: Individual RPC call timeout (conformance_check can be slow with many files)
        # OAuth can take 30-60s with user interaction (clicking, MFA, SSO redirects)
        self.client = FastMCPClient(
            transport=transport,
            auth=self.oauth,
            init_timeout=120.0,  # 2 minutes for OAuth + connection establishment
            timeout=75.0,  # 75 seconds for RPC calls (conformance checks can be slow)
        )

        # Connect with a generous timeout for OAuth flow
        # OAuth requires user interaction (clicking auth button, MFA, SSO)
        # Very generous timeout (5 minutes) to handle:
        # - User stepping away during auth
        # - Slow SSO redirects
        # - MFA delays
        # Better to wait longer than to cancel mid-auth and corrupt state
        try:
            await asyncio.wait_for(self.client.__aenter__(), timeout=300.0)
            echo("Successfully connected!", persona=Persona.DEVELOPER)
        except asyncio.TimeoutError:
            echo(f"Connection to {self.base_url} timed out after 5 minutes", err=True)
            echo(
                "This may be due to waiting for OAuth authentication.",
                persona=Persona.DEVELOPER,
                err=True,
            )
            raise APIError(
                f"Timeout connecting to MCP server at {self.base_url} - OAuth flow may have stalled"
            )
        except Exception as e:
            # Handle connection errors more gracefully
            error_msg = self._format_user_error(e)

            # Check if this is a transient error that might succeed on retry
            if is_transient_error(e):
                echo(f"Connection issue: {error_msg}", err=True)
                echo(
                    "The server may be experiencing temporary issues. Please try again in a moment.",
                    err=True,
                )
            else:
                echo(f"Unable to connect to {self.base_url}", err=True)
                echo(error_msg, err=True)

            # Show technical details for developers
            echo(
                f"Technical error: {type(e).__name__}: {e}",
                persona=Persona.DEVELOPER,
                err=True,
            )

            raise APIError(f"Failed to connect to MCP server at {self.base_url}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    @retry_on_error(
        max_retries=5,
        initial_delay=3.0,
        max_delay=60.0,
        backoff_factor=2.0,
        retryable_conditions=is_transient_error,
    )
    async def _call_tool_with_retry(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """
        Call an MCP tool with automatic retry on transient errors.

        This wraps the underlying client.call_tool() with retry logic to handle
        transient network errors like httpx.RemoteProtocolError.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            The tool result

        Raises:
            APIError: If the tool call fails after all retries
        """
        if not self.client:
            raise APIError("Client not initialized. Use async with statement.")

        return await self.client.call_tool(tool_name, arguments)

    def _format_user_error(self, error: Exception) -> str:
        """
        Format an exception into a user-friendly error message.

        Args:
            error: The exception to format

        Returns:
            A user-friendly error message
        """
        error_type = type(error).__name__
        error_str = str(error)

        # Handle timeout errors
        if "timeout" in error_type.lower() or "Timeout" in error_str.lower():
            return "The server is taking longer than expected. Please try again in a moment."

        # Handle connection errors
        if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
            return "Unable to reach the server. Please check your internet connection and try again."

        # Handle protocol errors
        if isinstance(error, httpx.RemoteProtocolError):
            return (
                "The server connection was interrupted. Please try again in a moment."
            )

        # Handle HTTP status errors
        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code
            if status == 429:
                return "Rate limit reached. Please wait a moment before trying again."
            elif 500 <= status < 600:
                # All 5xx errors get the same message
                return "The server is temporarily unavailable. Please try again in a moment."
            else:
                return f"Server returned error {status}. Please try again."

        # Handle MCP-specific errors and generic errors with same message
        # This covers ClientRequest timeouts and any other unexpected errors
        return "The server is temporarily unavailable. Please try again in a moment."

    async def check_conformance(
        self,
        files: list[dict[str, str]],
        batch_size: int = 5,
        show_progress: bool = True,
        ctx: Optional[click.Context] = None,
    ) -> list[dict[str, Any]]:
        """
        Call the conformance_check tool with the list of files.

        Args:
            files: List of file dictionaries with 'path' and 'content'
            batch_size: Maximum number of files to send at once (default 5, max 5)
            show_progress: Whether to show progress messages (default True)
            ctx: Optional Click context object containing configuration

        Returns:
            List of results for each batch with files
        """
        if not self.client:
            raise APIError("Client not initialized. Use async with statement.")

        # Enforce maximum batch size of 5
        if batch_size > 5:
            batch_size = 5

        all_results = []
        total_files = len(files)

        # Single file doesn't need batching
        if total_files == 1:
            echo("Processing single file", persona=Persona.DEVELOPER)
            try:
                result = await self._call_tool_with_retry(
                    "conformance_check", {"list_of_files": files}
                )
                echo("Received response from MCP server", persona=Persona.DEVELOPER)

                batch_results = {
                    "batch": 1,
                    "files": files,
                    "result": result,
                    "error": None,
                }
                all_results.append(batch_results)
            except Exception as e:
                # Log technical details for developers
                echo(
                    f"Technical error: {type(e).__name__}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )
                # Show user-friendly message
                error_msg = self._format_user_error(e)
                echo(f"✗ {error_msg}", err=True, log=False)
                batch_results = {
                    "batch": 1,
                    "files": files,
                    "result": None,
                    "error": error_msg,
                }
                all_results.append(batch_results)

            return all_results

        # Process multiple files in batches
        files_processed = 0
        files_with_issues = 0

        echo(
            f"Processing {total_files} files in batches of {batch_size}",
            persona=Persona.DEVELOPER,
        )
        for i in range(0, total_files, batch_size):
            batch = files[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            echo(
                f"Processing batch {batch_num} with {len(batch)} files",
                persona=Persona.DEVELOPER,
            )

            if show_progress:
                # Show progress
                echo(
                    f"\nChecking files {i + 1}-{min(i + len(batch), total_files)} of {total_files}...",
                    log=False,
                )

                # Show which files are in this batch
                for file_dict in batch:
                    file_path = Path(file_dict["path"])
                    # Try to make path relative to working directory
                    try:
                        rel_path = file_path.relative_to(Path.cwd())
                    except ValueError:
                        # If not relative to cwd, try relative to git root
                        try:
                            repo = git.Repo(search_parent_directories=True)
                            rel_path = file_path.relative_to(repo.working_dir)
                        except Exception:
                            rel_path = file_path
                    echo(f"  - {rel_path}", persona=Persona.POWER_USER)

            try:
                echo(
                    f"Calling conformance_check tool for batch {batch_num}",
                    persona=Persona.DEVELOPER,
                )
                result = await self._call_tool_with_retry(
                    "conformance_check", {"list_of_files": batch}
                )
                echo(
                    f"Received response for batch {batch_num}",
                    persona=Persona.DEVELOPER,
                )

                # Store batch with its files for later processing
                batch_results = {
                    "batch": batch_num,
                    "files": batch,
                    "result": result,
                    "error": None,
                }
                all_results.append(batch_results)

                if show_progress:
                    # Parse and show interim results
                    if (
                        hasattr(result, "content")
                        and result.content
                        and len(result.content) > 0
                    ):
                        content_text = (
                            result.content[0].text
                            if hasattr(result.content[0], "text")
                            else str(result.content[0])
                        ) or ""

                        # Try to parse the result to get file-specific information
                        try:
                            parsed_result = json.loads(content_text)
                            # Assume the result contains information about each file
                            if isinstance(parsed_result, dict):
                                # Count files with issues in this batch
                                batch_issues = 0
                                if "files" in parsed_result and parsed_result["files"]:
                                    for file_result in parsed_result["files"]:
                                        if file_result.get("issues", []):
                                            batch_issues += 1
                                elif (
                                    "issues" in parsed_result
                                    and parsed_result["issues"]
                                ):
                                    batch_issues = len(batch)

                                files_with_issues += batch_issues
                                files_processed += len(batch)

                                # Show running total
                                echo(
                                    f"Progress: {files_processed}/{total_files} files checked, {files_with_issues} with issues",
                                    log=False,
                                )
                        except (json.JSONDecodeError, KeyError):
                            files_processed += len(batch)
                            echo(
                                f"Progress: {files_processed}/{total_files} files checked",
                                log=False,
                            )
                    else:
                        files_processed += len(batch)
                        echo(
                            f"Progress: {files_processed}/{total_files} files checked",
                            log=False,
                        )

            except Exception as e:
                # Handle errors per batch
                # Log technical details for developers
                echo(
                    f"Technical error in batch {batch_num}: {type(e).__name__}",
                    persona=Persona.DEVELOPER,
                    err=True,
                )

                # Show user-friendly message
                error_msg = self._format_user_error(e)
                if show_progress:
                    echo(f"✗ {error_msg}", err=True, log=False)

                batch_results = {
                    "batch": batch_num,
                    "files": batch,
                    "result": None,
                    "error": error_msg,
                }
                all_results.append(batch_results)
                files_processed += len(batch)
                files_with_issues += len(batch)  # Count errored files as having issues

        return all_results

    def has_findings(
        self, parsed_result: Optional[dict[str, Any]], result_text: str = ""
    ) -> bool:
        """
        Check if the conformance result has any findings (issues).

        Args:
            parsed_result: Parsed JSON result from conformance check
            result_text: Raw text result as fallback

        Returns:
            True if there are findings/issues, False otherwise
        """
        if parsed_result:
            # Check for any non-PASS statuses
            for file_path, file_result in parsed_result.items():
                if isinstance(file_result, dict):
                    status = file_result.get("status", "")
                    if status != "PASS" and status:
                        return True
        elif result_text:
            # Fallback check if parsing failed
            # Check for overall result status
            if "Result: FAIL" in result_text:
                return True
            # Also check for check-level failures
            if any(
                indicator in result_text
                for indicator in [
                    ": `fail`",
                    "ERROR",
                    "WARNING",
                    "Finding:",
                ]
            ):
                return True
        return False


def parse_conformance_results(
    results: list[dict[str, Any]],
) -> tuple[list[str], bool, bool]:
    """
    Parse conformance check results and extract findings.

    Args:
        results: List of batch results from check_conformance

    Returns:
        Tuple of (all_results_text, has_errors, has_findings)
    """
    all_results = []
    has_errors = False
    has_findings = False
    failed_files = []

    # Create a temporary client instance to use has_findings method
    temp_client = ZenableMCPClient()

    for batch_result in results:
        if batch_result["error"]:
            has_errors = True
            # Track which files failed
            for file_dict in batch_result["files"]:
                failed_files.append(file_dict["path"])
        else:
            # Extract the text result from the MCP server
            result = batch_result["result"]
            if (
                hasattr(result, "content")
                and result.content
                and len(result.content) > 0
            ):
                content_text = (
                    result.content[0].text
                    if hasattr(result.content[0], "text")
                    else str(result.content[0])
                ) or ""
                all_results.append(content_text)

                # Check for findings in this batch
                try:
                    parsed = json.loads(content_text)
                    if isinstance(parsed, dict) and temp_client.has_findings(
                        parsed, content_text
                    ):
                        has_findings = True
                except (json.JSONDecodeError, KeyError):
                    # If we can't parse it, use the has_findings method with just text
                    if temp_client.has_findings(None, content_text):
                        has_findings = True
            else:
                all_results.append("No results returned")

    # Add summary of failed files at the end if any
    if failed_files:
        # Show basic summary to all users
        echo(
            f"\n⚠️  Unable to review {len(failed_files)} file(s). Please try again later.",
            log=False,
        )

        # Show detailed file list only in POWER_USER mode
        echo("\nFailed files:", persona=Persona.POWER_USER, log=False)
        for file_path in failed_files:
            # Make paths relative for readability
            try:
                rel_path = Path(file_path).relative_to(Path.cwd())
            except ValueError:
                rel_path = file_path
            echo(f"  - {rel_path}", persona=Persona.POWER_USER, log=False)

    return all_results, has_errors, has_findings


def extract_file_results(result: Any) -> Optional[dict[str, Any]]:
    """
    Extract file results from MCP server response.

    Args:
        result: Raw result from MCP server

    Returns:
        Parsed dictionary of file results or None
    """
    if not hasattr(result, "content") or not result.content:
        return None

    try:
        content_text = (
            result.content[0].text
            if hasattr(result.content[0], "text")
            else str(result.content[0])
        ) or ""
        return json.loads(content_text)
    except (json.JSONDecodeError, AttributeError, IndexError):
        return None
