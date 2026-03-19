"""Unified job management tool for monitoring Databricks job runs."""

from mcp.server.fastmcp import FastMCP

from src.auth import get_workspace_client
from src.job_runner import cancel_job, get_job_status, list_recent_runs


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def manage_jobs(
        action: str,
        run_id: str = "",
        limit: int = 20,
    ) -> str:
        """Manage Biomni bioinformatics tool jobs on Databricks.

        Args:
            action: One of 'status', 'list', or 'cancel'.
            run_id: Databricks run ID (required for 'status' and 'cancel').
            limit: Max number of runs to return (for 'list' only, default 20).
        """
        if action == "status":
            if not run_id:
                return "**Error:** 'status' requires a `run_id`."
            ws = get_workspace_client()
            status = await get_job_status(ws, run_id)
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

        elif action == "list":
            ws = get_workspace_client()
            runs = await list_recent_runs(ws, limit)
            if not runs:
                return "No recent Biomni jobs found."
            lines = ["## Recent Biomni Jobs\n"]
            for r in runs:
                state = r["state"]
                result = r.get("result_state") or ""
                display = f"{state}/{result}" if result else state
                lines.append(f"- **{r['run_name']}** (ID: {r['run_id']}) — {display}")
            return "\n".join(lines)

        elif action == "cancel":
            if not run_id:
                return "**Error:** 'cancel' requires a `run_id`."
            ws = get_workspace_client()
            msg = await cancel_job(ws, run_id)
            return msg

        else:
            return f"**Error:** Unknown action `{action}`. Use 'status', 'list', or 'cancel'."
