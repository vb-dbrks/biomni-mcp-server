"""Biomni MCP Server — bioinformatics CLI tools for Databricks."""

import logging
import os

import uvicorn
from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

from src.tools import register_all_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

mcp = FastMCP("BiomniTools")
workspace_client = WorkspaceClient()

register_all_tools(mcp, workspace_client)

app = mcp.streamable_http_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("DATABRICKS_APP_PORT", "8000")),
    )
