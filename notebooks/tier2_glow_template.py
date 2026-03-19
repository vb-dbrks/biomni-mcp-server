# Databricks notebook source
# MAGIC %md
# MAGIC # Biomni Tier 2: Glow Pipe Transformer Tool Execution
# MAGIC
# MAGIC This notebook is called by the Biomni MCP server to execute
# MAGIC stdin/stdout-compatible tools via the Glow Pipe Transformer.

# COMMAND ----------

# Parameters (set by notebook task base_parameters)
dbutils.widgets.text("tool", "")
dbutils.widgets.text("fastq_path", "")
dbutils.widgets.text("reference_genome_path", "")
dbutils.widgets.text("input_path", "")
dbutils.widgets.text("vcf_path", "")
dbutils.widgets.text("file_a", "")
dbutils.widgets.text("file_b", "")
dbutils.widgets.text("operation", "")
dbutils.widgets.text("filter_expression", "")
dbutils.widgets.text("output_path", "")

tool = dbutils.widgets.get("tool")
output_path = dbutils.widgets.get("output_path")

# COMMAND ----------

import json
from biomni_runner.glow_tools import GLOW_TOOLS

# Build params dict from widgets, filtering out empty values
all_params = {
    "fastq_path": dbutils.widgets.get("fastq_path"),
    "reference_genome_path": dbutils.widgets.get("reference_genome_path"),
    "input_path": dbutils.widgets.get("input_path"),
    "vcf_path": dbutils.widgets.get("vcf_path"),
    "file_a": dbutils.widgets.get("file_a"),
    "file_b": dbutils.widgets.get("file_b"),
    "operation": dbutils.widgets.get("operation"),
    "filter_expression": dbutils.widgets.get("filter_expression"),
    "output_path": output_path,
}
params = {k: v for k, v in all_params.items() if v}

tool_fn = GLOW_TOOLS[tool]
result = tool_fn(**params)
print(result)

# COMMAND ----------

# Set notebook exit value for the Jobs API
dbutils.notebook.exit(json.dumps({"status": "success", "output_path": output_path, "message": result}))
