"""Biomni MCP Server — bioinformatics CLI tools for Databricks."""

import logging
import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware

from src.auth import OBOAuthMiddleware
from src.tools import register_all_tools

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=__import__("sys").stdout,
    force=True,
)
print("=== Biomni MCP Server starting ===", flush=True)

# Allow Databricks workspace origins to connect
allowed_origins = ["*"]

mcp = FastMCP(
    "BiomniTools",
    stateless_http=True,
    json_response=True,
    log_level="DEBUG",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_origins=allowed_origins,
    ),
)

register_all_tools(mcp)

app = mcp.streamable_http_app()

# OBO middleware must be added before CORS so it runs on every request
app.add_middleware(OBOAuthMiddleware)
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
