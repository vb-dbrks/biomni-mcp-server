#!/bin/bash
# Upload init scripts to Unity Catalog Volumes
set -e

CATALOG="${BIOMNI_CATALOG:-bioinformatics}"
SCHEMA="${BIOMNI_SCHEMA:-tools}"
DEST="/Volumes/$CATALOG/$SCHEMA/init_scripts"

echo "=== Uploading init scripts ==="

for SCRIPT in cluster_scripts/*.sh; do
    BASENAME=$(basename "$SCRIPT")
    echo "Uploading $BASENAME to $DEST/"
    databricks fs cp "$SCRIPT" "dbfs:$DEST/$BASENAME" --overwrite
done

echo "=== Init scripts uploaded ==="
echo "Configure cluster init script path: $DEST/init_genomics_tools.sh"
