"""Base patterns for tool execution: safe subprocess, logging, error handling."""

import asyncio
import logging
import subprocess
from typing import Optional

logger = logging.getLogger("biomni")


async def safe_execute(
    cmd: list[str],
    *,
    input_data: Optional[str] = None,
    timeout: int = 300,
    cwd: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """Run a subprocess safely with timeout and logging.

    Raises subprocess.CalledProcessError on non-zero exit.
    Raises subprocess.TimeoutExpired on timeout.
    """
    logger.info("Executing: %s", " ".join(cmd))
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            input=input_data,
            cwd=cwd,
        ),
    )
    logger.info("Command completed (returncode=%d)", result.returncode)
    return result


def format_tool_result(
    tool_name: str,
    stdout: str = "",
    stderr: str = "",
    output_path: str = "",
) -> str:
    """Format a tool result as markdown for the MCP response."""
    parts = [f"## {tool_name}\n"]
    if stdout:
        parts.append(stdout.strip())
    if stderr:
        parts.append(f"\n### Warnings\n```\n{stderr.strip()}\n```")
    if output_path:
        parts.append(f"\n**Output:** `{output_path}`")
    return "\n".join(parts)


def format_error(tool_name: str, error: Exception) -> str:
    """Format a tool error as a readable message."""
    if isinstance(error, subprocess.CalledProcessError):
        return (
            f"**{tool_name} failed** (exit code {error.returncode})\n\n"
            f"```\n{error.stderr or error.stdout or str(error)}\n```"
        )
    if isinstance(error, subprocess.TimeoutExpired):
        return f"**{tool_name} timed out** after {error.timeout}s"
    return f"**{tool_name} error:** {error}"
