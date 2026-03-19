"""Tier 3 tools — file-based genomics tools running on cluster driver node."""

import os

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.job_runner import submit_notebook_job

NOTEBOOK_PATH = "/Workspace/biomni-tools/notebooks/tier3_driver_template"


def _job_submitted_msg(tool_name: str, run_id: str) -> str:
    return (
        f"## {tool_name}\n\n"
        f"Job submitted (Run ID: **{run_id}**).\n\n"
        f"Use `check_job_status('{run_id}')` to monitor progress."
    )


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    cluster_id = config.spark_cluster_id

    # ── MACS2 ──────────────────────────────────────────────────────────

    @mcp.tool()
    async def perform_chipseq_peak_calling_with_macs2(
        chip_seq_file: str,
        control_file: str,
        genome_size: str = "hs",
        q_value: float = 0.05,
        output_volume_path: str = f"{config.volume_base}/macs2_output",
    ) -> str:
        """Call ChIP-seq peaks using MACS2. Runs on cluster driver node.

        Args:
            chip_seq_file: Path to treatment BAM/BED file in a Volume.
            control_file: Path to control BAM/BED file in a Volume.
            genome_size: Effective genome size (hs, mm, ce, dm, or numeric).
            q_value: Minimum q-value cutoff (default 0.05).
            output_volume_path: Volume directory for peak files.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "macs2_peak_calling",
                "chip_seq_file": chip_seq_file,
                "control_file": control_file,
                "genome_size": genome_size,
                "q_value": str(q_value),
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("MACS2 Peak Calling", run_id)

    # ── HOMER ──────────────────────────────────────────────────────────

    @mcp.tool()
    async def find_enriched_motifs_with_homer(
        peak_file: str,
        genome: str = "hg38",
        size: int = 200,
        output_volume_path: str = f"{config.volume_base}/homer_output",
    ) -> str:
        """Find enriched DNA motifs in peak regions using HOMER.

        Args:
            peak_file: Path to BED/peak file in a Volume.
            genome: Reference genome (hg38, mm10, etc.).
            size: Fragment size for motif analysis (default 200bp).
            output_volume_path: Volume directory for motif results.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "homer_motif_finding",
                "peak_file": peak_file,
                "genome": genome,
                "size": str(size),
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("HOMER Motif Finding", run_id)

    # ── GATK / Mutect2 + SnpEff ────────────────────────────────────────

    @mcp.tool()
    async def detect_and_annotate_somatic_mutations(
        tumor_bam: str,
        normal_bam: str,
        reference_genome: str = "hg38",
        intervals: str = "",
        output_volume_path: str = f"{config.volume_base}/gatk_output",
    ) -> str:
        """Detect somatic mutations with GATK Mutect2 and annotate with SnpEff.

        Args:
            tumor_bam: Path to tumor BAM file in a Volume.
            normal_bam: Path to matched normal BAM file in a Volume.
            reference_genome: Reference genome name (hg38, mm10).
            intervals: Optional BED file or interval string for targeted regions.
            output_volume_path: Volume directory for VCF output.
        """
        ref_path = f"{config.genome_path}/{reference_genome}/{reference_genome}.fa"
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "gatk_mutect2_snpeff",
                "tumor_bam": tumor_bam,
                "normal_bam": normal_bam,
                "reference_path": ref_path,
                "intervals": intervals,
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("GATK Mutect2 + SnpEff", run_id)

    # ── LUMPY ──────────────────────────────────────────────────────────

    @mcp.tool()
    async def detect_and_characterize_structural_variations(
        bam_file: str,
        split_reads_bam: str = "",
        discordant_bam: str = "",
        output_volume_path: str = f"{config.volume_base}/lumpy_output",
    ) -> str:
        """Detect structural variants using LUMPY.

        Args:
            bam_file: Path to coordinate-sorted BAM file in a Volume.
            split_reads_bam: Optional path to split-read BAM.
            discordant_bam: Optional path to discordant-read BAM.
            output_volume_path: Volume directory for SV calls.
        """
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "lumpy_sv",
                "bam_file": bam_file,
                "split_reads_bam": split_reads_bam,
                "discordant_bam": discordant_bam,
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("LUMPY Structural Variant Detection", run_id)

    # ── CNVkit ─────────────────────────────────────────────────────────

    @mcp.tool()
    async def analyze_copy_number_purity_ploidy_and_focal_events(
        tumor_bam: str,
        normal_bam: str,
        reference_genome: str = "hg38",
        targets_bed: str = "",
        output_volume_path: str = f"{config.volume_base}/cnvkit_output",
    ) -> str:
        """Analyze copy number variations, purity, and ploidy using CNVkit.

        Args:
            tumor_bam: Path to tumor BAM file in a Volume.
            normal_bam: Path to matched normal BAM file in a Volume.
            reference_genome: Reference genome name (hg38, mm10).
            targets_bed: Optional BED file of target regions (for exome/panel data).
            output_volume_path: Volume directory for CNV results.
        """
        ref_path = f"{config.genome_path}/{reference_genome}/{reference_genome}.fa"
        run_id = await submit_notebook_job(
            workspace_client,
            notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "cnvkit_analysis",
                "tumor_bam": tumor_bam,
                "normal_bam": normal_bam,
                "reference_path": ref_path,
                "targets_bed": targets_bed,
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_submitted_msg("CNVkit Copy Number Analysis", run_id)
