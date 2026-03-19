"""File management tools for Unity Catalog Volumes."""

import base64
import json
import os

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.file_io import ensure_output_dir, list_files, read_file_head


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    @mcp.tool()
    async def list_volume_files(
        volume_path: str = config.volume_base,
    ) -> str:
        """List files in a Unity Catalog Volume directory.

        Args:
            volume_path: Absolute path under /Volumes/. Defaults to the workspace volume.
        """
        entries = list_files(volume_path)
        if not entries:
            return f"No files found in `{volume_path}` (or directory does not exist)."
        lines = [f"## Files in `{volume_path}`\n"]
        for e in entries:
            if e["is_dir"]:
                lines.append(f"- **{e['name']}/** (directory)")
            else:
                size = e.get("size_bytes", 0)
                if size >= 1_048_576:
                    display = f"{size / 1_048_576:.1f} MB"
                elif size >= 1024:
                    display = f"{size / 1024:.1f} KB"
                else:
                    display = f"{size} B"
                lines.append(f"- {e['name']}  ({display})")
        return "\n".join(lines)

    @mcp.tool()
    async def upload_file_to_volume(
        volume_path: str,
        content_base64: str,
        filename: str,
    ) -> str:
        """Upload a small file to Unity Catalog Volume (base64-encoded content).

        Args:
            volume_path: Target directory path under /Volumes/.
            content_base64: Base64-encoded file content.
            filename: Name for the uploaded file.
        """
        ensure_output_dir(volume_path)
        dest = os.path.join(volume_path, filename)
        data = base64.b64decode(content_base64)
        with open(dest, "wb") as f:
            f.write(data)
        return f"Uploaded `{filename}` ({len(data)} bytes) to `{volume_path}`"

    @mcp.tool()
    async def get_file_preview(
        volume_path: str,
        max_lines: int = 50,
    ) -> str:
        """Preview the first N lines of a text file in a Unity Catalog Volume.

        Args:
            volume_path: Absolute path to the file under /Volumes/.
            max_lines: Maximum number of lines to return (default 50).
        """
        if not os.path.isfile(volume_path):
            return f"File not found: `{volume_path}`"
        try:
            content = read_file_head(volume_path, max_lines)
            return f"## Preview: `{volume_path}`\n\n```\n{content}\n```"
        except UnicodeDecodeError:
            size = os.path.getsize(volume_path)
            return f"`{volume_path}` is a binary file ({size} bytes). Cannot preview as text."
