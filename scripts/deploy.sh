#!/bin/bash
# Deploy the Biomni MCP Server using Databricks Asset Bundles
set -e

TARGET="${1:-dev}"

echo "=== Validating bundle ==="
databricks bundle validate -t "$TARGET"

echo "=== Deploying to $TARGET ==="
databricks bundle deploy -t "$TARGET"

echo "=== Starting app ==="
databricks bundle run biomni_mcp -t "$TARGET"

echo "=== Deployment complete ==="
echo "Check status: databricks apps get mcp-biomni-tools"
