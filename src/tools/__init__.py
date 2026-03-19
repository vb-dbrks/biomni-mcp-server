"""Auto-registration of all tool modules."""

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP


def register_all_tools(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    """Register all tool modules with the MCP server."""
    from src.tools import (
        file_management,
        job_management,
        tier1_molecular,
        tier2_glow_pipe,
        tier3_genomics,
        tier3_microbiology,
        tier4_gpu,
    )

    file_management.register(mcp, workspace_client)
    job_management.register(mcp, workspace_client)
    tier1_molecular.register(mcp, workspace_client)
    tier2_glow_pipe.register(mcp, workspace_client)
    tier3_genomics.register(mcp, workspace_client)
    tier3_microbiology.register(mcp, workspace_client)
    tier4_gpu.register(mcp, workspace_client)
