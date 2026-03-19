"""End-to-end MCP protocol tests.

These tests verify the MCP server responds correctly to protocol messages.
Requires a running server or uses the FastMCP test client.
"""

import pytest


@pytest.mark.skip(reason="Requires running MCP server or full integration env")
class TestMcpEndToEnd:
    async def test_list_tools(self):
        """Verify all expected tools are listed."""
        # TODO: Connect to MCP server and call list_tools
        pass

    async def test_invoke_tier1_tool(self):
        """Invoke a Tier 1 tool and verify response format."""
        # TODO: Call predict_rna_secondary_structure with a test sequence
        pass

    async def test_invoke_tier2_tool(self):
        """Invoke a Tier 2 tool and verify job submission response."""
        # TODO: Call align_sequences_bwa with test params
        pass

    async def test_file_management(self):
        """Test file listing and preview."""
        # TODO: Upload a file, list it, preview it
        pass
