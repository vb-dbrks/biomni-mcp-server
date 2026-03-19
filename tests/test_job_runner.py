"""Tests for the Databricks job runner."""

import pytest

from src.job_runner import cancel_job, get_job_status, list_recent_runs, submit_notebook_job


@pytest.mark.asyncio
async def test_submit_notebook_job(mock_workspace_client):
    run_id = await submit_notebook_job(
        mock_workspace_client,
        notebook_path="/Workspace/biomni-tools/notebooks/test",
        parameters={"tool": "test_tool", "input": "/data/test.bam"},
        cluster_id="test-cluster-123",
    )
    assert run_id == "12345"
    mock_workspace_client.jobs.submit.assert_called_once()
    call_kwargs = mock_workspace_client.jobs.submit.call_args
    assert "biomni-test_tool" in call_kwargs.kwargs["run_name"]


@pytest.mark.asyncio
async def test_get_job_status(mock_workspace_client):
    status = await get_job_status(mock_workspace_client, "12345")
    assert status["run_id"] == "12345"
    assert status["state"] == "TERMINATED"
    assert status["result_state"] == "SUCCESS"
    mock_workspace_client.jobs.get_run.assert_called_once_with(12345)


@pytest.mark.asyncio
async def test_cancel_job(mock_workspace_client):
    result = await cancel_job(mock_workspace_client, "12345")
    assert "12345" in result
    mock_workspace_client.jobs.cancel_run.assert_called_once_with(12345)


@pytest.mark.asyncio
async def test_list_recent_runs_empty(mock_workspace_client):
    runs = await list_recent_runs(mock_workspace_client)
    assert runs == []
