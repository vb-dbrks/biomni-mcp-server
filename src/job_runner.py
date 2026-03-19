"""Databricks Jobs API wrapper for submitting Tier 2/3/4 workloads."""

import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import NotebookTask, SubmitTask


async def submit_notebook_job(
    workspace_client: WorkspaceClient,
    notebook_path: str,
    parameters: dict[str, str],
    cluster_id: str,
) -> str:
    """Submit a one-time notebook job and return the run ID."""
    run = workspace_client.jobs.submit(
        run_name=f"biomni-{parameters.get('tool', 'unknown')}-{int(time.time())}",
        tasks=[
            SubmitTask(
                task_key="main",
                existing_cluster_id=cluster_id,
                notebook_task=NotebookTask(
                    notebook_path=notebook_path,
                    base_parameters=parameters,
                ),
            )
        ],
    )
    return str(run.run_id)


async def get_job_status(
    workspace_client: WorkspaceClient,
    run_id: str,
) -> dict:
    """Get the current status of a job run."""
    run = workspace_client.jobs.get_run(int(run_id))
    result = {
        "run_id": run_id,
        "state": run.state.life_cycle_state.value if run.state else "UNKNOWN",
        "result_state": (
            run.state.result_state.value
            if run.state and run.state.result_state
            else None
        ),
        "run_page_url": run.run_page_url,
    }
    if run.state and run.state.state_message:
        result["message"] = run.state.state_message
    return result


async def cancel_job(
    workspace_client: WorkspaceClient,
    run_id: str,
) -> str:
    """Cancel a running job."""
    workspace_client.jobs.cancel_run(int(run_id))
    return f"Cancellation requested for run {run_id}"


async def list_recent_runs(
    workspace_client: WorkspaceClient,
    limit: int = 20,
) -> list[dict]:
    """List recent Biomni job runs."""
    runs = []
    for run in workspace_client.jobs.list_runs(limit=limit):
        if run.run_name and run.run_name.startswith("biomni-"):
            runs.append(
                {
                    "run_id": str(run.run_id),
                    "run_name": run.run_name,
                    "state": (
                        run.state.life_cycle_state.value if run.state else "UNKNOWN"
                    ),
                    "result_state": (
                        run.state.result_state.value
                        if run.state and run.state.result_state
                        else None
                    ),
                    "start_time": str(run.start_time) if run.start_time else None,
                }
            )
    return runs
