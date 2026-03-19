"""Unity Catalog Volume file I/O helpers."""

import os
from pathlib import Path

from databricks.sdk import WorkspaceClient

from src.config import config


def list_files(path: str) -> list[dict]:
    """List files in a Volume directory, returning name/size/modified metadata."""
    entries = []
    if not os.path.isdir(path):
        return entries
    for entry in sorted(os.scandir(path), key=lambda e: e.name):
        info = {"name": entry.name, "is_dir": entry.is_dir()}
        if not entry.is_dir():
            stat = entry.stat()
            info["size_bytes"] = stat.st_size
        entries.append(info)
    return entries


def read_file_head(path: str, max_lines: int = 50) -> str:
    """Read the first N lines of a text file."""
    lines: list[str] = []
    with open(path) as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                lines.append(f"\n... (truncated after {max_lines} lines)")
                break
            lines.append(line)
    return "".join(lines)


def write_text(path: str, content: str) -> str:
    """Write text content to a Volume path, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return path


def ensure_output_dir(path: str) -> str:
    """Ensure an output directory exists, creating it if needed."""
    os.makedirs(path, exist_ok=True)
    return path
