"""Auto-registration of all tool modules."""

from mcp.server.fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Register all functional bioinformatics tool modules with the MCP server."""
    from src.tools import (
        tier1_molecular,
        tier2_glow_pipe,
        tier3_genomics,
        tier3_microbiology,
        tier4_gpu,
    )

    tier1_molecular.register(mcp)
    tier2_glow_pipe.register(mcp)
    tier3_genomics.register(mcp)
    tier3_microbiology.register(mcp)
    tier4_gpu.register(mcp)
