"""Tier 3: File-based subprocess wrappers for driver-node execution."""

import os
import subprocess


def _run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)


def run_macs2_peak_calling(
    chip_seq_file: str,
    control_file: str,
    genome_size: str,
    q_value: str,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    result = _run([
        "macs2", "callpeak",
        "-t", chip_seq_file,
        "-c", control_file,
        "-g", genome_size,
        "-q", q_value,
        "--outdir", output_dir,
        "-n", "peaks",
    ])
    return f"MACS2 peak calling complete.\n{result.stdout}\nOutput: {output_dir}"


def run_homer_motif_finding(
    peak_file: str, genome: str, size: str, output_dir: str
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    result = _run([
        "findMotifsGenome.pl",
        peak_file, genome, output_dir,
        "-size", size,
    ])
    return f"HOMER motif finding complete.\n{result.stdout}\nOutput: {output_dir}"


def run_prokka_annotation(
    fasta_file: str,
    genus: str,
    species: str,
    strain: str,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    cmd = ["prokka", fasta_file, "--outdir", output_dir, "--prefix", "annotation", "--force"]
    if genus:
        cmd.extend(["--genus", genus])
    if species:
        cmd.extend(["--species", species])
    if strain:
        cmd.extend(["--strain", strain])
    result = _run(cmd)
    return f"Prokka annotation complete.\n{result.stdout}\nOutput: {output_dir}"


def run_gatk_mutect2_snpeff(
    tumor_bam: str,
    normal_bam: str,
    reference_path: str,
    intervals: str,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    raw_vcf = os.path.join(output_dir, "somatic_raw.vcf")
    filtered_vcf = os.path.join(output_dir, "somatic_filtered.vcf")
    annotated_vcf = os.path.join(output_dir, "somatic_annotated.vcf")

    # Mutect2
    cmd = [
        "gatk", "Mutect2",
        "-R", reference_path,
        "-I", tumor_bam,
        "-I", normal_bam,
        "-O", raw_vcf,
    ]
    if intervals:
        cmd.extend(["-L", intervals])
    _run(cmd)

    # FilterMutectCalls
    _run([
        "gatk", "FilterMutectCalls",
        "-R", reference_path,
        "-V", raw_vcf,
        "-O", filtered_vcf,
    ])

    # SnpEff annotation
    _run([
        "snpEff", "ann", "-v", "GRCh38.105",
        filtered_vcf,
        "-o", annotated_vcf,
    ], timeout=1800)

    return f"GATK Mutect2 + SnpEff pipeline complete.\nOutput: {output_dir}"


def run_lumpy_sv(
    bam_file: str,
    split_reads_bam: str,
    discordant_bam: str,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_vcf = os.path.join(output_dir, "sv_calls.vcf")
    cmd = ["lumpyexpress", "-B", bam_file, "-o", output_vcf]
    if split_reads_bam:
        cmd.extend(["-S", split_reads_bam])
    if discordant_bam:
        cmd.extend(["-D", discordant_bam])
    _run(cmd)
    return f"LUMPY SV detection complete.\nOutput: {output_vcf}"


def run_cnvkit_analysis(
    tumor_bam: str,
    normal_bam: str,
    reference_path: str,
    targets_bed: str,
    output_dir: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "cnvkit.py", "batch",
        tumor_bam,
        "--normal", normal_bam,
        "--fasta", reference_path,
        "--output-dir", output_dir,
    ]
    if targets_bed:
        cmd.extend(["--targets", targets_bed])
    else:
        cmd.append("--method")
        cmd.append("wgs")
    _run(cmd)
    return f"CNVkit analysis complete.\nOutput: {output_dir}"


FILE_TOOLS = {
    "macs2_peak_calling": run_macs2_peak_calling,
    "homer_motif_finding": run_homer_motif_finding,
    "prokka_annotation": run_prokka_annotation,
    "gatk_mutect2_snpeff": run_gatk_mutect2_snpeff,
    "lumpy_sv": run_lumpy_sv,
    "cnvkit_analysis": run_cnvkit_analysis,
}
