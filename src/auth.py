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
    """Pure ASGI middleware for OBO auth.

    Lazily creates a WorkspaceClient only when get_workspace_client() is
    actually called (i.e., Tier 2/3/4 tools). Tier 1 tools don't call it,
    so no WorkspaceClient is created for them — zero overhead.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Store the token in a context var — client created lazily on first use
        headers = dict(scope.get("headers", []))
        user_token = headers.get(b"x-forwarded-access-token", b"").decode() or None

        if user_token:
            host = os.environ.get("DATABRICKS_HOST", "")
            # Create a lazy wrapper that builds the client only when accessed
            _user_token_var.set((host, user_token))
        else:
            _user_token_var.set(None)

        await self.app(scope, receive, send)


# Lazy token storage — avoids creating WorkspaceClient on every request
_user_token_var: contextvars.ContextVar[tuple[str, str] | None] = contextvars.ContextVar(
    "user_token", default=None
)


def get_workspace_client() -> WorkspaceClient:
    """Get the WorkspaceClient for the current request.

    Lazily creates an OBO client from the stored user token, or falls
    back to the service principal. Only called by Tier 2/3/4 tools.
    """
    token_info = _user_token_var.get(None)
    if token_info is not None:
        host, token = token_info
        cfg = Config(host=host, token=token, auth_type="pat")
        return WorkspaceClient(config=cfg)
    return _get_sp_client()
