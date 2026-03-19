"""Biomni MCP Server — bioinformatics CLI tools for Databricks."""

import logging
import os

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.tools import register_all_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

mcp = FastMCP("BiomniTools")
workspace_client = WorkspaceClient()

register_all_tools(mcp, workspace_client)

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.getenv("DATABRICKS_APP_PORT", "8000")),
    )
