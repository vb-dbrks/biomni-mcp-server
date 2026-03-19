"""Tier 3 — genomics tools running on cluster driver node."""

from mcp.server.fastmcp import FastMCP

from src.auth import get_workspace_client
from src.config import config
from src.job_runner import submit_notebook_job

NOTEBOOK_PATH = "/Workspace/biomni-tools/notebooks/tier3_driver_template"


def _job_msg(tool_name: str, run_id: str) -> str:
    return (
        f"## {tool_name}\n\n"
        f"Job submitted (Run ID: **{run_id}**).\n\n"
        f"Use `manage_jobs(action='status', run_id='{run_id}')` to monitor."
    )


def register(mcp: FastMCP) -> None:
    cluster_id = config.spark_cluster_id

    @mcp.tool()
    async def run_chipseq_analysis(
        tool: str,
        input_file: str,
        output_volume_path: str = f"{config.volume_base}/chipseq_output",
        control_file: str = "",
        genome: str = "hg38",
        genome_size: str = "hs",
        q_value: float = 0.05,
        motif_size: int = 200,
    ) -> str:
        """Run ChIP-seq analysis: peak calling (MACS2) or motif finding (HOMER).

        Args:
            tool: 'macs2' for peak calling or 'homer' for motif enrichment.
            input_file: For macs2: treatment BAM/BED file. For homer: BED/peak file.
            output_volume_path: Volume directory for results.
            control_file: Control BAM/BED file (required for macs2).
            genome: Reference genome for homer (hg38, mm10).
            genome_size: Effective genome size for macs2 (hs, mm, ce, dm, or numeric).
            q_value: Q-value cutoff for macs2 (default 0.05).
            motif_size: Fragment size for homer motif analysis (default 200bp).
        """
        if tool == "macs2":
            if not control_file:
                return "**Error:** MACS2 requires a `control_file`."
            ws = get_workspace_client()
            run_id = await submit_notebook_job(
                ws, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "macs2_peak_calling",
                    "chip_seq_file": input_file, "control_file": control_file,
                    "genome_size": genome_size, "q_value": str(q_value),
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("MACS2 Peak Calling", run_id)

        elif tool == "homer":
            ws = get_workspace_client()
            run_id = await submit_notebook_job(
                ws, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "homer_motif_finding",
                    "peak_file": input_file, "genome": genome,
                    "size": str(motif_size), "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("HOMER Motif Finding", run_id)

        else:
            return f"**Error:** Unknown tool `{tool}`. Use 'macs2' or 'homer'."

    @mcp.tool()
    async def run_somatic_mutation_pipeline(
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
        ws = get_workspace_client()
        run_id = await submit_notebook_job(
            ws, notebook_path=NOTEBOOK_PATH,
            parameters={
                "tool": "gatk_mutect2_snpeff",
                "tumor_bam": tumor_bam, "normal_bam": normal_bam,
                "reference_path": ref_path, "intervals": intervals,
                "output_dir": output_volume_path,
            },
            cluster_id=cluster_id,
        )
        return _job_msg("GATK Mutect2 + SnpEff", run_id)

    @mcp.tool()
    async def run_structural_variant_analysis(
        tool: str,
        input_bam: str,
        output_volume_path: str = f"{config.volume_base}/sv_output",
        normal_bam: str = "",
        reference_genome: str = "hg38",
        split_reads_bam: str = "",
        discordant_bam: str = "",
        targets_bed: str = "",
    ) -> str:
        """Detect structural variants (LUMPY) or analyze copy number (CNVkit).

        Args:
            tool: 'lumpy' for structural variant detection or 'cnvkit' for copy number analysis.
            input_bam: Tumor/sample BAM file path in a Volume.
            output_volume_path: Volume directory for results.
            normal_bam: Matched normal BAM (required for cnvkit).
            reference_genome: Reference genome for cnvkit (hg38, mm10).
            split_reads_bam: Split-read BAM for lumpy (optional).
            discordant_bam: Discordant-read BAM for lumpy (optional).
            targets_bed: Target regions BED for cnvkit exome/panel data (optional).
        """
        if tool == "lumpy":
            ws = get_workspace_client()
            run_id = await submit_notebook_job(
                ws, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "lumpy_sv",
                    "bam_file": input_bam,
                    "split_reads_bam": split_reads_bam,
                    "discordant_bam": discordant_bam,
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("LUMPY Structural Variant Detection", run_id)

        elif tool == "cnvkit":
            if not normal_bam:
                return "**Error:** CNVkit requires a `normal_bam`."
            ref_path = f"{config.genome_path}/{reference_genome}/{reference_genome}.fa"
            ws = get_workspace_client()
            run_id = await submit_notebook_job(
                ws, notebook_path=NOTEBOOK_PATH,
                parameters={
                    "tool": "cnvkit_analysis",
                    "tumor_bam": input_bam, "normal_bam": normal_bam,
                    "reference_path": ref_path, "targets_bed": targets_bed,
                    "output_dir": output_volume_path,
                },
                cluster_id=cluster_id,
            )
            return _job_msg("CNVkit Copy Number Analysis", run_id)

        else:
            return f"**Error:** Unknown tool `{tool}`. Use 'lumpy' or 'cnvkit'."
