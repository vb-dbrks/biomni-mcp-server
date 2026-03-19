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
from databricks.sdk.config import Config
from starlette.types import ASGIApp, Receive, Scope, Send

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


class OBOAuthMiddleware:
    """Pure ASGI middleware — no BaseHTTPMiddleware (avoids streaming issues).

    Extracts X-Forwarded-Access-Token from request headers and sets a
    per-request WorkspaceClient via contextvars before passing to the app.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        user_token = headers.get(b"x-forwarded-access-token", b"").decode() or None
        user_email = headers.get(b"x-forwarded-email", b"unknown").decode()

        if user_token:
            host = os.environ.get("DATABRICKS_HOST", "")
            cfg = Config(host=host, token=user_token, auth_type="pat")
            client = WorkspaceClient(config=cfg)
            _workspace_client_var.set(client)
            logger.info("OBO auth: running as user %s", user_email)
        else:
            _workspace_client_var.set(_get_sp_client())

        await self.app(scope, receive, send)
