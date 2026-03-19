#!/bin/bash
# Deploy the Biomni MCP Server as a Databricks App
set -e

APP_NAME="${1:-biomni-tools}"

echo "=== Deploying Biomni MCP Server as Databricks App ==="

# Sync source to workspace
databricks workspace import-dir . "/Workspace/biomni-tools" --overwrite

# Deploy the app
databricks apps deploy "$APP_NAME" --source-code-path "/Workspace/biomni-tools"

echo "=== Deployment complete ==="
echo "App: $APP_NAME"
echo "Check status: databricks apps get $APP_NAME"
