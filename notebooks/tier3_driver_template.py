# Databricks notebook source
# MAGIC %md
# MAGIC # Biomni Tier 3: Driver-Node Tool Execution
# MAGIC
# MAGIC This notebook is called by the Biomni MCP server to execute
# MAGIC file-based bioinformatics tools on the cluster driver node.

# COMMAND ----------

# Parameters (set by notebook task base_parameters)
dbutils.widgets.text("tool", "")
dbutils.widgets.text("chip_seq_file", "")
dbutils.widgets.text("control_file", "")
dbutils.widgets.text("genome_size", "hs")
dbutils.widgets.text("q_value", "0.05")
dbutils.widgets.text("peak_file", "")
dbutils.widgets.text("genome", "hg38")
dbutils.widgets.text("size", "200")
dbutils.widgets.text("fasta_file", "")
dbutils.widgets.text("genus", "")
dbutils.widgets.text("species", "")
dbutils.widgets.text("strain", "")
dbutils.widgets.text("tumor_bam", "")
dbutils.widgets.text("normal_bam", "")
dbutils.widgets.text("reference_path", "")
dbutils.widgets.text("intervals", "")
dbutils.widgets.text("bam_file", "")
dbutils.widgets.text("split_reads_bam", "")
dbutils.widgets.text("discordant_bam", "")
dbutils.widgets.text("targets_bed", "")
dbutils.widgets.text("output_dir", "")

tool = dbutils.widgets.get("tool")
output_dir = dbutils.widgets.get("output_dir")

# COMMAND ----------

import json
from biomni_runner.file_tools import FILE_TOOLS

# Collect all widget values, filtering out empty strings
widget_names = [
    "chip_seq_file", "control_file", "genome_size", "q_value",
    "peak_file", "genome", "size",
    "fasta_file", "genus", "species", "strain",
    "tumor_bam", "normal_bam", "reference_path", "intervals",
    "bam_file", "split_reads_bam", "discordant_bam",
    "targets_bed", "output_dir",
]
params = {k: dbutils.widgets.get(k) for k in widget_names if dbutils.widgets.get(k)}

tool_fn = FILE_TOOLS[tool]
result = tool_fn(**params)
print(result)

# COMMAND ----------

dbutils.notebook.exit(json.dumps({"status": "success", "output_dir": output_dir, "message": result}))
