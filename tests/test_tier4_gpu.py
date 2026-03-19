"""Tests for Tier 4 GPU tools (mocked job submission)."""

import pytest

from src.job_runner import submit_notebook_job


@pytest.mark.asyncio
async def test_nnunet_job_submission(mock_workspace_client):
    run_id = await submit_notebook_job(
        mock_workspace_client,
        notebook_path="/Workspace/biomni-tools/notebooks/tier4_gpu_template",
        parameters={
            "tool": "nnunet_segment",
            "image_path": "/Volumes/bio/tools/data/scan.nii.gz",
            "task_id": "Task001_BrainTumour",
            "model_type": "3d_fullres",
            "output_dir": "/Volumes/bio/tools/workspace_files/nnunet_output",
        },
        cluster_id="test-gpu-cluster",
    )
    assert run_id == "12345"


@pytest.mark.asyncio
async def test_diffdock_job_submission(mock_workspace_client):
    run_id = await submit_notebook_job(
        mock_workspace_client,
        notebook_path="/Workspace/biomni-tools/notebooks/tier4_gpu_template",
        parameters={
            "tool": "diffdock_predict",
            "protein_pdb_path": "/Volumes/bio/tools/data/protein.pdb",
            "ligand_smiles": "CC(=O)Oc1ccccc1C(=O)O",
            "num_poses": "10",
            "output_dir": "/Volumes/bio/tools/workspace_files/diffdock_output",
        },
        cluster_id="test-gpu-cluster",
    )
    assert run_id == "12345"
