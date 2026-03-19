"""Tier 2: Glow Pipe Transformer wrappers for stdin/stdout-compatible tools."""


def run_bwa_alignment(fastq_path: str, reference_genome_path: str, output_path: str) -> str:
    """Align reads with BWA via Glow pipe transformer."""
    import glow
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    glow.register(spark)

    df = spark.read.format("text").load(fastq_path)
    aligned_df = glow.transform(
        "pipe",
        df,
        cmd=["bwa", "mem", "-t", "4", reference_genome_path, "-"],
        input_formatter="text",
        output_formatter="text",
    )
    aligned_df.write.mode("overwrite").text(output_path)
    return f"BWA alignment complete. Output: {output_path}"


def run_samtools_process(input_path: str, operation: str, output_path: str) -> str:
    """Process alignments with Samtools via Glow pipe transformer."""
    import glow
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    glow.register(spark)

    df = spark.read.format("binaryFile").load(input_path)

    cmd_map = {
        "sort": ["samtools", "sort", "-"],
        "view": ["samtools", "view", "-h", "-"],
        "flagstat": ["samtools", "flagstat", "-"],
    }
    cmd = cmd_map.get(operation, ["samtools", operation, "-"])

    result_df = glow.transform(
        "pipe", df, cmd=cmd, input_formatter="text", output_formatter="text"
    )
    result_df.write.mode("overwrite").text(output_path)
    return f"Samtools {operation} complete. Output: {output_path}"


def run_bcftools_filter(vcf_path: str, filter_expression: str, output_path: str) -> str:
    """Filter VCF with BCFtools via Glow pipe transformer."""
    import glow
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    glow.register(spark)

    df = spark.read.format("text").load(vcf_path)
    filtered_df = glow.transform(
        "pipe",
        df,
        cmd=["bcftools", "view", "-i", filter_expression, "-"],
        input_formatter="text",
        output_formatter="text",
    )
    filtered_df.write.mode("overwrite").text(output_path)
    return f"BCFtools filter complete. Output: {output_path}"


def run_bedtools_operation(
    file_a: str, file_b: str, operation: str, output_path: str
) -> str:
    """Run Bedtools operation via Glow pipe transformer."""
    import glow
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    glow.register(spark)

    df = spark.read.format("text").load(file_a)
    result_df = glow.transform(
        "pipe",
        df,
        cmd=["bedtools", operation, "-a", "stdin", "-b", file_b],
        input_formatter="text",
        output_formatter="text",
    )
    result_df.write.mode("overwrite").text(output_path)
    return f"Bedtools {operation} complete. Output: {output_path}"


GLOW_TOOLS = {
    "bwa_alignment": run_bwa_alignment,
    "samtools_process": run_samtools_process,
    "bcftools_filter": run_bcftools_filter,
    "bedtools_operation": run_bedtools_operation,
}
