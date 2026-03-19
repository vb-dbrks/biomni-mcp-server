"""Configuration for Biomni MCP Server."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BiomniConfig:
    """Server configuration loaded from environment variables."""

    catalog: str = os.getenv("BIOMNI_CATALOG", "bioinformatics")
    schema: str = os.getenv("BIOMNI_SCHEMA", "tools")
    volume: str = os.getenv("BIOMNI_VOLUME", "workspace_files")
    ref_volume: str = os.getenv("BIOMNI_REF_VOLUME", "reference_data")
    spark_cluster_id: str = os.getenv("SPARK_CLUSTER_ID", "")
    gpu_cluster_id: str = os.getenv("GPU_CLUSTER_ID", "")

    @property
    def volume_base(self) -> str:
        return f"/Volumes/{self.catalog}/{self.schema}/{self.volume}"

    @property
    def ref_volume_base(self) -> str:
        return f"/Volumes/{self.catalog}/{self.schema}/{self.ref_volume}"

    @property
    def genome_path(self) -> str:
        return f"{self.ref_volume_base}/genomes"

    @property
    def model_path(self) -> str:
        return f"{self.ref_volume_base}/models"


config = BiomniConfig()
