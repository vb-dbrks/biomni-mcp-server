#!/bin/bash
# Init script for Databricks cluster: installs bioinformatics CLI tools
# Upload to: /Volumes/bioinformatics/tools/init_scripts/init_genomics_tools.sh
set -e

echo "=== Installing bioinformatics tools via conda ==="

conda install -y -c bioconda -c conda-forge \
    bwa=0.7.17 \
    samtools=1.19 \
    bcftools=1.19 \
    bedtools=2.31.1 \
    macs2=2.2.9.1 \
    homer=4.11 \
    prokka=1.14.6 \
    gatk4=4.5.0.0 \
    snpsift=5.2 \
    snpeff=5.2 \
    lumpy-sv=0.3.1 \
    cnvkit=0.9.10

echo "=== Installing Glow ==="
pip install glow.py

echo "=== Verifying installations ==="
which bwa && bwa 2>&1 | head -1
which samtools && samtools --version | head -1
which bcftools && bcftools --version | head -1
which bedtools && bedtools --version
which macs2 && macs2 --version
which prokka && prokka --version
which gatk && gatk --version 2>&1 | head -1
which lumpyexpress
which cnvkit.py && cnvkit.py version

echo "=== Init script complete ==="
