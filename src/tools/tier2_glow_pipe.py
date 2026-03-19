"""Tier 2 tools — distributed execution via Glow Pipe Transformer on Spark."""

import os

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.job_runner import submit_notebook_job

NOTEBOOK_PATH = "/Workspace/biomni-tools/notebooks/tier2_glow_template"


def _job_submitted_msg(tool_name: str, run_id: str) -> str:
    return (
        f"## {tool_name}\n\n"
        f"Job submitted (Run ID: **{run_id}**).\n\n"
        f"Use `check_job_status('{run_id}')` to monitor progress."
    )


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    cluster_id = config.spark_cluster_id

    @mcp.tool()
    async def align_sequences_bwa(
        fastq_path: str,
        reference_genome: str = "hg38",
        output_volume_path: str = f"{config.volume_base}/bwa_output",
    ) -> str:
        """Align sequencing reads using BWA via Glow Pipe Transformer (distributed Spark).

        Args:
            fastq_path: Path to FASTQ file(s) in a Volume.
            reference_genome: Reference genome name (hg38, mm10, etc.).
            output_volume_path: Volume directory for aligned SAM/BAM output.
        """
        ref_path = f"{config.genome_path}/{reference_genome}/{reference_genome}.fa"
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "bwa_alignment",
                "fastq_path": fastq_path,
                "reference_genome_path": ref_path,
                "output_path": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("BWA Alignment (Glow Pipe)", run_id)

    @mcp.tool()
    async def process_alignments_samtools(
        input_path: str,
        operation: str = "sort",
        output_volume_path: str = f"{config.volume_base}/samtools_output",
    ) -> str:
        """Process alignment files using Samtools via Glow Pipe Transformer.

        Args:
            input_path: Path to SAM/BAM file in a Volume.
            operation: Samtools operation — sort, index, flagstat, view, etc.
            output_volume_path: Volume directory for processed output.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "samtools_process",
                "input_path": input_path,
                "operation": operation,
                "output_path": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg(f"Samtools ({operation})", run_id)

    @mcp.tool()
    async def filter_variants_bcftools(
        vcf_path: str,
        filter_expression: str = "QUAL>20",
        output_volume_path: str = f"{config.volume_base}/bcftools_output",
    ) -> str:
        """Filter and process VCF variant files using BCFtools via Glow Pipe Transformer.

        Args:
            vcf_path: Path to VCF file in a Volume.
            filter_expression: BCFtools filter expression (e.g. 'QUAL>20').
            output_volume_path: Volume directory for filtered output.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "bcftools_filter",
                "vcf_path": vcf_path,
                "filter_expression": filter_expression,
                "output_path": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("BCFtools Filter (Glow Pipe)", run_id)

    @mcp.tool()
    async def intersect_regions_bedtools(
        file_a: str,
        file_b: str,
        operation: str = "intersect",
        output_volume_path: str = f"{config.volume_base}/bedtools_output",
    ) -> str:
        """Perform genomic interval operations using Bedtools via Glow Pipe Transformer.

        Args:
            file_a: Path to first BED/BAM/VCF file in a Volume.
            file_b: Path to second BED/BAM/VCF file in a Volume.
            operation: Bedtools operation — intersect, subtract, merge, etc.
            output_volume_path: Volume directory for output.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "bedtools_operation",
                "file_a": file_a,
                "file_b": file_b,
                "operation": operation,
                "output_path": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg(f"Bedtools ({operation})", run_id)
