"""On-behalf-of (OBO) authentication for Databricks Apps.

When a user calls the MCP server through Genie Code or another client,
the Databricks Apps proxy injects an X-Forwarded-Access-Token header
containing the user's OAuth token. We use this to create a per-request
WorkspaceClient that runs API calls as the user — so Volume access,
job submissions, and audit logs all reflect the user's identity.

Falls back to the app's service principal when no user token is present
(e.g., local development, direct API calls).
"""

import contextvars
import logging
import os

from databricks.sdk import WorkspaceClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("biomni.auth")

# Context variable holding the per-request WorkspaceClient
_workspace_client_var: contextvars.ContextVar[WorkspaceClient] = contextvars.ContextVar(
    "workspace_client"
)

# Fallback service principal client (used when no user token)
_sp_client: WorkspaceClient | None = None


def _get_sp_client() -> WorkspaceClient:
    """Get or create the service principal WorkspaceClient (singleton)."""
    global _sp_client
    if _sp_client is None:
        _sp_client = WorkspaceClient()
    return _sp_client


def get_workspace_client() -> WorkspaceClient:
    """Get the WorkspaceClient for the current request.

    Returns the user's OBO client if available, otherwise the SP client.
    Call this from tool implementations instead of using a global client.
    """
    try:
        return _workspace_client_var.get()
    except LookupError:
        return _get_sp_client()


class OBOAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that creates a per-request WorkspaceClient from the user's token."""

    async def dispatch(self, request: Request, call_next):
        user_token = request.headers.get("X-Forwarded-Access-Token")
        user_email = request.headers.get("X-Forwarded-Email", "unknown")

        if user_token:
            host = os.environ.get("DATABRICKS_HOST", "")
            client = WorkspaceClient(host=host, token=user_token)
            _workspace_client_var.set(client)
            logger.info("OBO auth: running as user %s", user_email)
        else:
            _workspace_client_var.set(_get_sp_client())
            logger.debug("No user token — using service principal")

        response = await call_next(request)
        return response
