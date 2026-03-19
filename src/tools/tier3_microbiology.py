"""Tier 3 tools — microbiology (Prokka) running on cluster driver node."""

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.job_runner import submit_notebook_job

NOTEBOOK_PATH = "/Workspace/biomni-tools/notebooks/tier3_driver_template"


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    cluster_id = config.spark_cluster_id

    @mcp.tool()
    async def annotate_bacterial_genome(
        fasta_file: str,
        genus: str = "",
        species: str = "",
        strain: str = "",
        output_volume_path: str = f"{config.volume_base}/prokka_output",
    ) -> str:
        """Annotate a bacterial genome using Prokka.

        Args:
            fasta_file: Path to assembled contigs FASTA file in a Volume.
            genus: Optional genus name for annotation database selection.
            species: Optional species name.
            strain: Optional strain name.
            output_volume_path: Volume directory for annotation output.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "prokka_annotation",
                "fasta_file": fasta_file,
                "genus": genus,
                "species": species,
                "strain": strain,
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return (
            f"## Prokka Bacterial Genome Annotation\n\n"
            f"Job submitted (Run ID: **{run_id}**).\n\n"
            f"Use `check_job_status('{run_id}')` to monitor progress."
        )
