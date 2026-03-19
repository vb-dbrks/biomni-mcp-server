"""Unified file management tool for Unity Catalog Volumes."""

import base64
import os

from mcp.server.fastmcp import FastMCP

from src.config import config
from src.file_io import ensure_output_dir, list_files, read_file_head


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def manage_volume_files(
        action: str,
        volume_path: str = config.volume_base,
        content_base64: str = "",
        filename: str = "",
        max_lines: int = 50,
    ) -> str:
        """Manage files in Unity Catalog Volumes.

        Args:
            action: One of 'list', 'upload', or 'preview'.
            volume_path: Volume path. For 'list': directory to list. For 'upload': target directory. For 'preview': file path.
            content_base64: Base64-encoded file content (required for 'upload').
            filename: Name for uploaded file (required for 'upload').
            max_lines: Max lines to preview (default 50, for 'preview' only).
        """
        if action == "list":
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

        elif action == "upload":
            if not content_base64 or not filename:
                return "**Error:** 'upload' requires both `content_base64` and `filename`."
            ensure_output_dir(volume_path)
            dest = os.path.join(volume_path, filename)
            data = base64.b64decode(content_base64)
            with open(dest, "wb") as f:
                f.write(data)
            return f"Uploaded `{filename}` ({len(data)} bytes) to `{volume_path}`"

        elif action == "preview":
            if not os.path.isfile(volume_path):
                return f"File not found: `{volume_path}`"
            try:
                content = read_file_head(volume_path, max_lines)
                return f"## Preview: `{volume_path}`\n\n```\n{content}\n```"
            except UnicodeDecodeError:
                size = os.path.getsize(volume_path)
                return f"`{volume_path}` is a binary file ({size} bytes). Cannot preview as text."

        else:
            return f"**Error:** Unknown action `{action}`. Use 'list', 'upload', or 'preview'."
