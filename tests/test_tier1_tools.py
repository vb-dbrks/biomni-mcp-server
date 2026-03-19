"""Tests for Tier 1 in-app tools (mocked subprocess)."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.tool_wrapper import format_error, format_tool_result, safe_execute


@pytest.mark.asyncio
async def test_safe_execute_success():
    """Test safe_execute with a simple command."""
    result = await safe_execute(["echo", "hello"])
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0


@pytest.mark.asyncio
async def test_safe_execute_failure():
    """Test safe_execute raises on non-zero exit."""
    with pytest.raises(subprocess.CalledProcessError):
        await safe_execute(["false"])


@pytest.mark.asyncio
async def test_safe_execute_timeout():
    """Test safe_execute respects timeout."""
    with pytest.raises(subprocess.TimeoutExpired):
        await safe_execute(["sleep", "10"], timeout=1)


def test_format_tool_result():
    result = format_tool_result(
        "Test Tool",
        stdout="output data",
        output_path="/Volumes/test/output.txt",
    )
    assert "## Test Tool" in result
    assert "output data" in result
    assert "/Volumes/test/output.txt" in result


def test_format_error_called_process():
    err = subprocess.CalledProcessError(1, "cmd", stderr="bad input")
    msg = format_error("MyTool", err)
    assert "MyTool failed" in msg
    assert "bad input" in msg


def test_format_error_timeout():
    err = subprocess.TimeoutExpired("cmd", 60)
    msg = format_error("MyTool", err)
    assert "timed out" in msg
    assert "60" in msg
