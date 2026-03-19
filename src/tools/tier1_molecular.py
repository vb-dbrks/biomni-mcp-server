"""Tier 1 tools — run directly in the App container via subprocess."""

import os
import tempfile

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.file_io import ensure_output_dir, write_text
from src.tool_wrapper import format_error, format_tool_result, safe_execute
from src.validation import (
    ValidationError,
    validate_rna_sequence,
    validate_smiles,
    validate_volume_file,
    validate_volume_path,
)


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    # ── ViennaRNA ──────────────────────────────────────────────────────

    @mcp.tool()
    async def predict_rna_secondary_structure(
        rna_sequence: str,
        output_volume_path: str = f"{config.volume_base}/rna_output",
    ) -> str:
        """Predict RNA secondary structure using ViennaRNA RNAfold.

        Args:
            rna_sequence: RNA sequence string (ACGU characters).
            output_volume_path: Volume directory to write results.
        """
        try:
            rna_sequence = validate_rna_sequence(rna_sequence)
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fa", delete=False
        ) as f:
            f.write(f">input\n{rna_sequence}\n")
            input_path = f.name
        try:
            result = await safe_execute(
                ["RNAfold", "-i", input_path], timeout=120
            )
            ensure_output_dir(output_volume_path)
            out_file = os.path.join(output_volume_path, "rnafold_result.txt")
            write_text(out_file, result.stdout)
            return format_tool_result(
                "RNA Structure Prediction (ViennaRNA)",
                stdout=result.stdout,
                stderr=result.stderr,
                output_path=out_file,
            )
        except Exception as e:
            return format_error("ViennaRNA RNAfold", e)
        finally:
            os.unlink(input_path)

    # ── pLannotate ─────────────────────────────────────────────────────

    @mcp.tool()
    async def annotate_plasmid(
        sequence_file: str,
        output_volume_path: str = f"{config.volume_base}/plannotate_output",
    ) -> str:
        """Annotate a plasmid DNA sequence using pLannotate.

        Args:
            sequence_file: Path to a FASTA/GenBank file in a Volume.
            output_volume_path: Volume directory to write annotated output.
        """
        try:
            validate_volume_file(sequence_file)
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"
        ensure_output_dir(output_volume_path)
        try:
            result = await safe_execute(
                [
                    "plannotate",
                    "batch",
                    "-i", sequence_file,
                    "-o", output_volume_path,
                ],
                timeout=300,
            )
            return format_tool_result(
                "Plasmid Annotation (pLannotate)",
                stdout=result.stdout,
                stderr=result.stderr,
                output_path=output_volume_path,
            )
        except Exception as e:
            return format_error("pLannotate", e)

    # ── MUSCLE (alignment) ─────────────────────────────────────────────

    @mcp.tool()
    async def analyze_protein_conservation(
        fasta_file: str,
        output_volume_path: str = f"{config.volume_base}/muscle_output",
    ) -> str:
        """Perform multiple sequence alignment using MUSCLE to analyze protein conservation.

        Args:
            fasta_file: Path to a multi-FASTA file in a Volume.
            output_volume_path: Volume directory for alignment output.
        """
        try:
            validate_volume_file(fasta_file)
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"
        ensure_output_dir(output_volume_path)
        out_file = os.path.join(output_volume_path, "alignment.afa")
        try:
            result = await safe_execute(
                ["muscle", "-in", fasta_file, "-out", out_file],
                timeout=600,
            )
            return format_tool_result(
                "Protein Conservation (MUSCLE alignment)",
                stdout=result.stdout,
                stderr=result.stderr,
                output_path=out_file,
            )
        except Exception as e:
            return format_error("MUSCLE", e)

    # ── MUSCLE (phylogeny) ─────────────────────────────────────────────

    @mcp.tool()
    async def analyze_protein_phylogeny(
        fasta_file: str,
        output_volume_path: str = f"{config.volume_base}/phylogeny_output",
    ) -> str:
        """Build a phylogenetic tree from protein sequences using MUSCLE.

        Args:
            fasta_file: Path to a multi-FASTA file in a Volume.
            output_volume_path: Volume directory for tree output.
        """
        try:
            validate_volume_file(fasta_file)
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"
        ensure_output_dir(output_volume_path)
        alignment_file = os.path.join(output_volume_path, "alignment.afa")
        tree_file = os.path.join(output_volume_path, "tree.nwk")
        try:
            await safe_execute(
                ["muscle", "-in", fasta_file, "-out", alignment_file],
                timeout=600,
            )
            result = await safe_execute(
                [
                    "muscle",
                    "-maketree",
                    "-in", alignment_file,
                    "-out", tree_file,
                    "-cluster", "neighborjoining",
                ],
                timeout=300,
            )
            return format_tool_result(
                "Protein Phylogeny (MUSCLE)",
                stdout=f"Alignment: `{alignment_file}`\nTree: `{tree_file}`",
                stderr=result.stderr,
                output_path=tree_file,
            )
        except Exception as e:
            return format_error("MUSCLE phylogeny", e)

    # ── BLAST ──────────────────────────────────────────────────────────

    @mcp.tool()
    async def blast_sequence(
        sequence: str,
        database: str = "nr",
        program: str = "blastp",
        max_hits: int = 10,
        output_volume_path: str = f"{config.volume_base}/blast_output",
    ) -> str:
        """Search for similar sequences using NCBI BLAST+.

        For local BLAST: uses blastp/blastn against a local database.
        For remote BLAST: uses -remote flag to query NCBI servers.

        Args:
            sequence: Query sequence (amino acid or nucleotide).
            database: BLAST database name (nr, nt, swissprot, etc.).
            program: BLAST program (blastp, blastn, blastx, tblastn).
            max_hits: Maximum number of alignments to report.
            output_volume_path: Volume directory for results.
        """
        VALID_PROGRAMS = {"blastp", "blastn", "blastx", "tblastn", "tblastx"}
        if program not in VALID_PROGRAMS:
            return f"**Validation error:** Invalid BLAST program: {program}. Use one of: {', '.join(sorted(VALID_PROGRAMS))}"
        try:
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"
        ensure_output_dir(output_volume_path)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fa", delete=False
        ) as f:
            f.write(f">query\n{sequence}\n")
            query_path = f.name
        out_file = os.path.join(output_volume_path, "blast_results.txt")
        try:
            result = await safe_execute(
                [
                    program,
                    "-query", query_path,
                    "-db", database,
                    "-remote",
                    "-outfmt", "6",
                    "-max_target_seqs", str(max_hits),
                    "-out", out_file,
                ],
                timeout=600,
            )
            with open(out_file) as fh:
                content = fh.read()
            return format_tool_result(
                f"BLAST Search ({program} vs {database})",
                stdout=content or "(no hits found)",
                stderr=result.stderr,
                output_path=out_file,
            )
        except Exception as e:
            return format_error(f"BLAST ({program})", e)
        finally:
            os.unlink(query_path)

    # ── PyLabRobot ─────────────────────────────────────────────────────

    @mcp.tool()
    async def test_pylabrobot_script(
        script_content: str,
        output_volume_path: str = f"{config.volume_base}/pylabrobot_output",
    ) -> str:
        """Test a PyLabRobot automation script in simulation mode.

        Runs the provided Python script that uses PyLabRobot for liquid
        handling robot control (simulation only, no real hardware).

        Args:
            script_content: Python source code using PyLabRobot APIs.
            output_volume_path: Volume directory for any output files.
        """
        ensure_output_dir(output_volume_path)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=output_volume_path
        ) as f:
            f.write(script_content)
            script_path = f.name
        try:
            result = await safe_execute(
                ["python", script_path],
                timeout=120,
                cwd=output_volume_path,
            )
            return format_tool_result(
                "PyLabRobot Simulation",
                stdout=result.stdout,
                stderr=result.stderr,
                output_path=output_volume_path,
            )
        except Exception as e:
            return format_error("PyLabRobot", e)
        finally:
            os.unlink(script_path)
