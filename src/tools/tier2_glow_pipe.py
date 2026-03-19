"""Tier 2 — unified alignment pipeline tool via Glow Pipe Transformer."""

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.job_runner import submit_notebook_job

NOTEBOOK_PATH = "/Workspace/biomni-tools/notebooks/tier2_glow_template"


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    cluster_id = config.spark_cluster_id

    @mcp.tool()
    async def run_alignment_pipeline(
        tool: str,
        input_path: str,
        output_volume_path: str = f"{config.volume_base}/alignment_output",
        reference_genome: str = "hg38",
        second_input_path: str = "",
        operation: str = "",
        filter_expression: str = "",
    ) -> str:
        """Run distributed genomic alignment and processing tools via Glow Pipe Transformer on Spark.

        Args:
            tool: Tool to run — 'bwa' (align reads), 'samtools' (process alignments), 'bcftools' (filter variants), or 'bedtools' (interval operations).
            input_path: Path to input file in a Volume (FASTQ for bwa, SAM/BAM for samtools, VCF for bcftools, BED/BAM for bedtools).
            output_volume_path: Volume directory for output.
            reference_genome: Reference genome name for bwa (hg38, mm10). Ignored by other tools.
            second_input_path: Second input file for bedtools interval operations (file B).
            operation: Operation type — for samtools: sort/index/flagstat/view. For bedtools: intersect/subtract/merge.
            filter_expression: Filter expression for bcftools (e.g. 'QUAL>20').
        """
        VALID_TOOLS = {"bwa", "samtools", "bcftools", "bedtools"}
        if tool not in VALID_TOOLS:
            return f"**Error:** Unknown tool `{tool}`. Use: {', '.join(sorted(VALID_TOOLS))}"

        if tool == "bwa":
            ref_path = f"{config.genome_path}/{reference_genome}/{reference_genome}.fa"
            params = {
                "tool": "bwa_alignment",
                "fastq_path": input_path,
                "reference_genome_path": ref_path,
                "output_path": output_volume_path,
            }
        elif tool == "samtools":
            params = {
                "tool": "samtools_process",
                "input_path": input_path,
                "operation": operation or "sort",
                "output_path": output_volume_path,
            }
        elif tool == "bcftools":
            params = {
                "tool": "bcftools_filter",
                "vcf_path": input_path,
                "filter_expression": filter_expression or "QUAL>20",
                "output_path": output_volume_path,
            }
        elif tool == "bedtools":
            if not second_input_path:
                return "**Error:** bedtools requires `second_input_path` (file B)."
            params = {
                "tool": "bedtools_operation",
                "file_a": input_path,
                "file_b": second_input_path,
                "operation": operation or "intersect",
                "output_path": output_volume_path,
            }

        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters=params,
            cluster_id=cluster_id,
        )
        tool_display = {"bwa": "BWA Alignment", "samtools": f"Samtools ({operation or 'sort'})",
                        "bcftools": "BCFtools Filter", "bedtools": f"Bedtools ({operation or 'intersect'})"}
        return (
            f"## {tool_display[tool]} (Glow Pipe)\n\n"
            f"Job submitted (Run ID: **{run_id}**).\n\n"
            f"Use `manage_jobs(action='status', run_id='{run_id}')` to monitor."
        )
