# Biomni MCP Server

MCP server exposing 18 bioinformatics CLI tools as Databricks App.

## Architecture

4-tier execution model:
- **Tier 1** (in-app subprocess): ViennaRNA, pLannotate, MUSCLE, BLAST+, PyLabRobot
- **Tier 2** (Glow Pipe Transformer on Spark): BWA, Samtools, BCFtools, Bedtools
- **Tier 3** (cluster driver subprocess): MACS2, HOMER, Prokka, GATK, LUMPY, CNVkit, SnpEff
- **Tier 4** (GPU Container Services): nnUNet, DiffDock, Cellpose, AutoDock Vina, AutoSite

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Key directories

- `src/` — MCP server code (config, file_io, job_runner, tool_wrapper)
- `src/tools/` — MCP tool definitions grouped by tier
- `runner/` — Cluster-side execution package (installed on Databricks clusters)
- `notebooks/` — Parameterized Databricks notebook templates
- `cluster_scripts/` — Init scripts for cluster tool installation
- `docker/` — GPU Dockerfile for Container Services
- `scripts/` — Deployment and setup scripts

## Conventions

- Tools return markdown-formatted strings
- Tier 2/3/4 tools are async (submit job, return run ID)
- All file I/O uses Unity Catalog Volume paths (`/Volumes/...`)
- Tests mock `WorkspaceClient` and subprocess calls
