"""Tests for Tier 3 genomics tools (mocked job submission)."""

import pytest

from src.job_runner import submit_notebook_job


@pytest.mark.asyncio
async def test_macs2_job_submission(mock_workspace_client):
    run_id = await submit_notebook_job(
        mock_workspace_client,
        notebook_path="/Workspace/biomni-tools/notebooks/tier3_driver_template",
        parameters={
            "tool": "macs2_peak_calling",
            "chip_seq_file": "/Volumes/bio/tools/data/chip.bam",
            "control_file": "/Volumes/bio/tools/data/control.bam",
            "genome_size": "hs",
            "q_value": "0.05",
            "output_dir": "/Volumes/bio/tools/workspace_files/macs2_output",
        },
        cluster_id="test-cluster",
    )
    assert run_id == "12345"


@pytest.mark.asyncio
async def test_gatk_job_submission(mock_workspace_client):
    run_id = await submit_notebook_job(
        mock_workspace_client,
        notebook_path="/Workspace/biomni-tools/notebooks/tier3_driver_template",
        parameters={
            "tool": "gatk_mutect2_snpeff",
            "tumor_bam": "/Volumes/bio/tools/data/tumor.bam",
            "normal_bam": "/Volumes/bio/tools/data/normal.bam",
            "reference_path": "/Volumes/bio/ref/genomes/hg38/hg38.fa",
            "intervals": "",
            "output_dir": "/Volumes/bio/tools/workspace_files/gatk_output",
        },
        cluster_id="test-cluster",
    )
    assert run_id == "12345"
