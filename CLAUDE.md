# Biomni MCP Server

MCP server exposing 18 bioinformatics CLI tools as a Databricks App.

## Architecture

4-tier execution model:
- **Tier 1** (in-app Python packages): ViennaRNA, pLannotate, BioPython (MUSCLE/BLAST), PyLabRobot
- **Tier 2** (Glow Pipe Transformer on Spark): BWA, Samtools, BCFtools, Bedtools
- **Tier 3** (cluster driver subprocess): MACS2, HOMER, Prokka, GATK, LUMPY, CNVkit, SnpEff
- **Tier 4** (GPU Container Services): nnUNet, DiffDock, Cellpose, AutoDock Vina, AutoSite

**Important:** Databricks Apps do NOT support custom Dockerfiles. Tier 1 tools must use
pip-installable Python packages only. System binaries (apt-get) are not available.

## Deployment

Uses Databricks Asset Bundles (DAB):
```bash
# Set cluster IDs in databricks.yml variables first
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle run biomni_mcp -t dev
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Key directories

- `src/` — MCP server code (config, file_io, job_runner, tool_wrapper, validation)
- `src/tools/` — MCP tool definitions grouped by tier
- `runner/` — Cluster-side execution package (installed on Databricks clusters)
- `notebooks/` — Parameterized Databricks notebook templates
- `cluster_scripts/` — Init scripts for cluster tool installation
- `docker/` — GPU Dockerfile for Container Services (Tier 4 only)
- `scripts/` — Deployment and setup scripts

## Conventions

- Tools return markdown-formatted strings
- Tier 1 tools use Python packages directly (no subprocess for bio tools)
- Tier 2/3/4 tools are async (submit job, return run ID)
- All file I/O uses Unity Catalog Volume paths (`/Volumes/...`)
- Input validation via `src/validation.py` (sequences, paths, genomes)
- Tests mock `WorkspaceClient` and subprocess calls
