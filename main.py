"""Biomni MCP Server — bioinformatics CLI tools for Databricks."""

import logging
import os

import uvicorn
from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware

from src.tools import register_all_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# Allow Databricks workspace origins to connect
databricks_host = os.getenv("DATABRICKS_HOST", "")
allowed_origins = ["*"]
if databricks_host:
    allowed_origins.append(databricks_host.rstrip("/"))

mcp = FastMCP(
    "BiomniTools",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_origins=allowed_origins,
    ),
)
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
