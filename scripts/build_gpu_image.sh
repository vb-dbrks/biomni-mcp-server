#!/bin/bash
# Build and push the GPU Docker image for Tier 4 tools
set -e

REGISTRY="${1:?Usage: $0 <registry-url> [tag]}"
TAG="${2:-latest}"
IMAGE="$REGISTRY/biomni-gpu:$TAG"

echo "=== Building GPU Docker image ==="
docker build -f docker/Dockerfile.gpu -t "$IMAGE" .

echo "=== Pushing to registry ==="
docker push "$IMAGE"

echo "=== Done ==="
echo "Image: $IMAGE"
echo "Configure this in your GPU cluster's Container Services settings."
