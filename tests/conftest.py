"""Shared test fixtures for Biomni MCP Server tests."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_workspace_client():
    """Mock Databricks WorkspaceClient."""
    client = MagicMock()
    # Mock jobs API
    mock_run = MagicMock()
    mock_run.run_id = 12345
    client.jobs.submit.return_value = mock_run

    mock_status = MagicMock()
    mock_status.state.life_cycle_state.value = "TERMINATED"
    mock_status.state.result_state.value = "SUCCESS"
    mock_status.state.state_message = "Completed"
    mock_status.run_page_url = "https://workspace.databricks.com/run/12345"
    client.jobs.get_run.return_value = mock_status

    client.jobs.list_runs.return_value = []
    return client


@pytest.fixture(autouse=True)
def set_env_vars():
    """Set environment variables for testing."""
    with patch.dict(os.environ, {
        "BIOMNI_CATALOG": "bioinformatics",
        "BIOMNI_SCHEMA": "tools",
        "BIOMNI_VOLUME": "workspace_files",
        "SPARK_CLUSTER_ID": "test-cluster-id",
        "GPU_CLUSTER_ID": "test-gpu-cluster-id",
    }):
        yield
