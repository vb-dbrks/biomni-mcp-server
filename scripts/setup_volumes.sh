#!/bin/bash
# Create Unity Catalog Volumes for Biomni tools
set -e

CATALOG="${BIOMNI_CATALOG:-bioinformatics}"
SCHEMA="${BIOMNI_SCHEMA:-tools}"

echo "=== Setting up Unity Catalog Volumes ==="

# Create catalog and schema if needed
databricks unity-catalog catalogs create --name "$CATALOG" 2>/dev/null || true
databricks unity-catalog schemas create --catalog-name "$CATALOG" --name "$SCHEMA" 2>/dev/null || true

# Create volumes
for VOLUME in workspace_files reference_data init_scripts; do
    echo "Creating volume: $CATALOG.$SCHEMA.$VOLUME"
    databricks unity-catalog volumes create \
        --catalog-name "$CATALOG" \
        --schema-name "$SCHEMA" \
        --name "$VOLUME" \
        --volume-type MANAGED 2>/dev/null || true
done

echo "=== Creating reference data directory structure ==="
REF_BASE="/Volumes/$CATALOG/$SCHEMA/reference_data"
for DIR in genomes/hg38 genomes/mm10 snpeff/data models/nnunet models/cellpose models/diffdock annotations/cosmic annotations/clinvar; do
    databricks fs mkdirs "dbfs:$REF_BASE/$DIR" 2>/dev/null || true
done

echo "=== Volume setup complete ==="
echo "Workspace files: /Volumes/$CATALOG/$SCHEMA/workspace_files"
echo "Reference data:  /Volumes/$CATALOG/$SCHEMA/reference_data"
echo "Init scripts:    /Volumes/$CATALOG/$SCHEMA/init_scripts"
