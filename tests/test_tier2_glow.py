"""Tests for Tier 2 Glow pipe tools (mocked job submission)."""

import pytest

from src.job_runner import submit_notebook_job


@pytest.mark.asyncio
async def test_bwa_job_submission(mock_workspace_client):
    """Test that BWA alignment submits a notebook job with correct params."""
    run_id = await submit_notebook_job(
        mock_workspace_client,
        notebook_path="/Workspace/biomni-tools/notebooks/tier2_glow_template",
        parameters={
            "tool": "bwa_alignment",
            "fastq_path": "/Volumes/bio/tools/data/reads.fastq",
            "reference_genome_path": "/Volumes/bio/ref/genomes/hg38/hg38.fa",
            "output_path": "/Volumes/bio/tools/workspace_files/bwa_output",
        },
        cluster_id="test-cluster",
    )
    assert run_id == "12345"


@pytest.mark.asyncio
async def test_bcftools_job_submission(mock_workspace_client):
    """Test BCFtools filter job submission."""
    run_id = await submit_notebook_job(
        mock_workspace_client,
        notebook_path="/Workspace/biomni-tools/notebooks/tier2_glow_template",
        parameters={
            "tool": "bcftools_filter",
            "vcf_path": "/Volumes/bio/tools/data/variants.vcf",
            "filter_expression": "QUAL>20",
            "output_path": "/Volumes/bio/tools/workspace_files/bcftools_output",
        },
        cluster_id="test-cluster",
    )
    assert run_id == "12345"
