"""Tests for MCP tool registration — verify all expected tools are registered."""

from unittest.mock import MagicMock, patch

import pytest

from mcp.server.fastmcp import FastMCP


@pytest.fixture
def mcp_with_tools():
    """Create a FastMCP instance with all tools registered."""
    mcp = FastMCP("TestBiomniTools")
    client = MagicMock()  # mock WorkspaceClient

    from src.tools import register_all_tools
    register_all_tools(mcp, client)
    return mcp


EXPECTED_TOOLS = [
    # File management
    "list_volume_files",
    "upload_file_to_volume",
    "get_file_preview",
    # Job management
    "check_job_status",
    "list_biomni_jobs",
    "cancel_biomni_job",
    # Tier 1
    "predict_rna_secondary_structure",
    "annotate_plasmid",
    "analyze_protein_conservation",
    "analyze_protein_phylogeny",
    "blast_sequence",
    "test_pylabrobot_script",
    # Tier 2
    "align_sequences_bwa",
    "process_alignments_samtools",
    "filter_variants_bcftools",
    "intersect_regions_bedtools",
    # Tier 3
    "perform_chipseq_peak_calling_with_macs2",
    "find_enriched_motifs_with_homer",
    "detect_and_annotate_somatic_mutations",
    "detect_and_characterize_structural_variations",
    "analyze_copy_number_purity_ploidy_and_focal_events",
    "annotate_bacterial_genome",
    # Tier 4
    "segment_with_nn_unet",
    "run_diffdock_with_smiles",
    "segment_cells_with_deep_learning",
    "docking_autodock_vina",
    "run_autosite",
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
    """Verify total tool count matches expected (27 tools)."""
    registered = mcp_with_tools._tool_manager._tools
    assert len(registered) == len(EXPECTED_TOOLS), (
        f"Expected {len(EXPECTED_TOOLS)} tools, got {len(registered)}: "
        f"{sorted(registered.keys())}"
    )
