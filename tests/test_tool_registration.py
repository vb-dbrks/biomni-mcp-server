"""Tests for MCP tool registration — verify all expected tools are registered."""

from unittest.mock import MagicMock

import pytest

from mcp.server.fastmcp import FastMCP


@pytest.fixture
def mcp_with_tools():
    """Create a FastMCP instance with all tools registered."""
    mcp = FastMCP("TestBiomniTools")

    from src.tools import register_all_tools
    register_all_tools(mcp)
    return mcp


EXPECTED_TOOLS = [
    # Tier 1 — in-app Python packages (6)
    "predict_rna_secondary_structure",
    "annotate_plasmid",
    "analyze_protein_conservation",
    "analyze_protein_phylogeny",
    "blast_sequence",
    "test_pylabrobot_script",
    # Tier 2 — Glow pipe (1 consolidated)
    "run_alignment_pipeline",
    # Tier 3 — driver node (4: chipseq, somatic, structural, prokka)
    "run_chipseq_analysis",
    "run_somatic_mutation_pipeline",
    "run_structural_variant_analysis",
    "annotate_bacterial_genome",
    # Tier 4 — GPU (2 consolidated)
    "run_medical_imaging",
    "run_molecular_docking",
]


def test_all_tools_registered(mcp_with_tools):
    """Verify every expected tool is registered."""
    registered = set(mcp_with_tools._tool_manager._tools.keys())
    for tool_name in EXPECTED_TOOLS:
        assert tool_name in registered, f"Tool '{tool_name}' not registered"


def test_no_extra_tools(mcp_with_tools):
    """Verify no unexpected tools are registered."""
    registered = set(mcp_with_tools._tool_manager._tools.keys())
    expected = set(EXPECTED_TOOLS)
    extra = registered - expected
    assert not extra, f"Unexpected tools registered: {extra}"


def test_tool_count(mcp_with_tools):
    """Verify total tool count is within Genie Code limit of 15."""
    registered = mcp_with_tools._tool_manager._tools
    assert len(registered) == len(EXPECTED_TOOLS), (
        f"Expected {len(EXPECTED_TOOLS)} tools, got {len(registered)}: "
        f"{sorted(registered.keys())}"
    )
    assert len(registered) <= 15, f"Exceeds Genie Code 15-tool limit: {len(registered)} tools"
