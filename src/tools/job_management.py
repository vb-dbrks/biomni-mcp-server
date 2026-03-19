"""Job management tools for monitoring Databricks job runs."""

import json

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.job_runner import cancel_job, get_job_status, list_recent_runs


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    @mcp.tool()
    async def check_job_status(run_id: str) -> str:
        """Check the status of a submitted Biomni tool job.

        Args:
            run_id: The Databricks run ID returned when the job was submitted.
        """
        status = await get_job_status(workspace_client, run_id)
        state = status["state"]
        result = status.get("result_state")
        url = status.get("run_page_url", "")

        lines = [f"## Job Status: Run {run_id}\n"]
        lines.append(f"- **State:** {state}")
        if result:
            lines.append(f"- **Result:** {result}")
        if status.get("message"):
            lines.append(f"- **Message:** {status['message']}")
        if url:
            lines.append(f"- **Details:** [View in Databricks]({url})")
        return "\n".join(lines)

    @mcp.tool()
    async def list_biomni_jobs(limit: int = 20) -> str:
        """List recent Biomni tool job runs.

        Args:
            limit: Maximum number of runs to return (default 20).
        """
        runs = await list_recent_runs(workspace_client, limit)
        if not runs:
            return "No recent Biomni jobs found."
        lines = ["## Recent Biomni Jobs\n"]
        for r in runs:
            state = r["state"]
            result = r.get("result_state") or ""
            display = f"{state}/{result}" if result else state
            lines.append(f"- **{r['run_name']}** (ID: {r['run_id']}) — {display}")
        return "\n".join(lines)

    @mcp.tool()
    async def cancel_biomni_job(run_id: str) -> str:
        """Cancel a running Biomni tool job.

        Args:
            run_id: The Databricks run ID to cancel.
        """
        msg = await cancel_job(workspace_client, run_id)
        return msg
