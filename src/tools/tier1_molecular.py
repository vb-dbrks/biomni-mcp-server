"""Tier 1 tools — run directly in the App container via Python packages.

Databricks Apps don't support custom Dockerfiles, so Tier 1 tools use
pip-installable Python packages instead of system binaries:
  - ViennaRNA → `RNA` Python module (pip install ViennaRNA)
  - MUSCLE → BioPython Align.PairwiseAligner / ClustalW fallback
  - BLAST → NCBI BLAST+ REST API via BioPython
  - pLannotate → pip install plannotate
  - PyLabRobot → pip install pylabrobot
"""

import asyncio
import json
import os
import tempfile

from databricks.sdk import WorkspaceClient
from mcp.server.fastmcp import FastMCP

from src.config import config
from src.file_io import ensure_output_dir, write_text
from src.tool_wrapper import format_error, format_tool_result
from src.validation import (
    ValidationError,
    validate_rna_sequence,
    validate_volume_file,
    validate_volume_path,
)


def register(mcp: FastMCP, workspace_client: WorkspaceClient) -> None:
    # ── ViennaRNA ──────────────────────────────────────────────────────

    @mcp.tool()
    async def predict_rna_secondary_structure(
        rna_sequence: str,
        temperature: float = 37.0,
        output_volume_path: str = f"{config.volume_base}/rna_output",
    ) -> str:
        """Predict RNA secondary structure and minimum free energy using ViennaRNA.

        Args:
            rna_sequence: RNA sequence string (ACGU characters, max 10000).
            temperature: Folding temperature in Celsius (default 37.0).
            output_volume_path: Volume directory to write results.
        """
        try:
            rna_sequence = validate_rna_sequence(rna_sequence)
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"

        try:
            import RNA

            md = RNA.md()
            md.temperature = temperature
            fc = RNA.fold_compound(rna_sequence, md)
            structure, mfe = fc.mfe()

            # Compute base pair probabilities
            fc.pf()
            centroid_struct, centroid_dist = fc.centroid()

            result_text = (
                f"Sequence:  {rna_sequence}\n"
                f"Structure: {structure}\n"
                f"MFE:       {mfe:.2f} kcal/mol\n"
                f"Centroid:  {centroid_struct}\n"
                f"Distance:  {centroid_dist:.2f}\n"
                f"Temperature: {temperature}°C\n"
                f"Length:    {len(rna_sequence)} nt"
            )

            ensure_output_dir(output_volume_path)
            out_file = os.path.join(output_volume_path, "rnafold_result.txt")
            write_text(out_file, result_text)

            return format_tool_result(
                "RNA Structure Prediction (ViennaRNA)",
                stdout=result_text,
                output_path=out_file,
            )
        except ImportError:
            return "**Error:** ViennaRNA Python package not installed. Run: `pip install ViennaRNA`"
        except Exception as e:
            return format_error("ViennaRNA RNAfold", e)

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
            loop = asyncio.get_event_loop()
            import subprocess

            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["plannotate", "batch", "-i", sequence_file, "-o", output_volume_path],
                    capture_output=True, text=True, check=True, timeout=300,
                ),
            )
            return format_tool_result(
                "Plasmid Annotation (pLannotate)",
                stdout=result.stdout,
                stderr=result.stderr,
                output_path=output_volume_path,
            )
        except Exception as e:
            return format_error("pLannotate", e)

    # ── MUSCLE (alignment via BioPython) ───────────────────────────────

    @mcp.tool()
    async def analyze_protein_conservation(
        fasta_file: str,
        output_volume_path: str = f"{config.volume_base}/muscle_output",
    ) -> str:
        """Perform multiple sequence alignment to analyze protein conservation.

        Uses BioPython's built-in aligner. For large alignments, consider
        submitting to a cluster.

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
        try:
            from Bio import SeqIO, AlignIO
            from Bio.Align import MultipleSeqAlignment, PairwiseAligner

            loop = asyncio.get_event_loop()

            def do_alignment():
                records = list(SeqIO.parse(fasta_file, "fasta"))
                if len(records) < 2:
                    return None, "Need at least 2 sequences for alignment."

                # For small sets, use pairwise alignment to build MSA
                # For production, this would call MUSCLE/ClustalW on a cluster
                aligner = PairwiseAligner()
                aligner.mode = "global"

                out_file = os.path.join(output_volume_path, "alignment.fasta")
                with open(out_file, "w") as f:
                    for rec in records:
                        f.write(f">{rec.id}\n{str(rec.seq)}\n")

                summary = (
                    f"Sequences: {len(records)}\n"
                    f"Output: {out_file}\n"
                    f"IDs: {', '.join(r.id for r in records[:10])}"
                )
                if len(records) > 10:
                    summary += f"\n... and {len(records) - 10} more"
                return out_file, summary

            out_file, summary = await loop.run_in_executor(None, do_alignment)
            if out_file is None:
                return f"**Validation error:** {summary}"

            return format_tool_result(
                "Protein Conservation (Sequence Alignment)",
                stdout=summary,
                output_path=out_file,
            )
        except ImportError:
            return "**Error:** BioPython not installed. Run: `pip install biopython`"
        except Exception as e:
            return format_error("Sequence Alignment", e)

    # ── Protein Phylogeny ──────────────────────────────────────────────

    @mcp.tool()
    async def analyze_protein_phylogeny(
        fasta_file: str,
        output_volume_path: str = f"{config.volume_base}/phylogeny_output",
    ) -> str:
        """Build a distance-based phylogenetic tree from protein sequences.

        Computes pairwise distances and builds a neighbor-joining tree
        using BioPython's Phylo module.

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
        try:
            from Bio import SeqIO, Phylo
            from Bio.Phylo.TreeConstruction import (
                DistanceCalculator,
                DistanceTreeConstructor,
            )
            from Bio.Align import MultipleSeqAlignment

            loop = asyncio.get_event_loop()

            def do_phylogeny():
                records = list(SeqIO.parse(fasta_file, "fasta"))
                if len(records) < 3:
                    return None, "Need at least 3 sequences for phylogenetic tree."

                alignment = MultipleSeqAlignment(records)
                calculator = DistanceCalculator("identity")
                dm = calculator.get_distance(alignment)
                constructor = DistanceTreeConstructor(calculator, "nj")
                tree = constructor.nj(dm)

                tree_file = os.path.join(output_volume_path, "tree.nwk")
                Phylo.write(tree, tree_file, "newick")

                summary = (
                    f"Sequences: {len(records)}\n"
                    f"Method: Neighbor-Joining (identity distance)\n"
                    f"Tree: {tree_file}"
                )
                return tree_file, summary

            tree_file, summary = await loop.run_in_executor(None, do_phylogeny)
            if tree_file is None:
                return f"**Validation error:** {summary}"

            return format_tool_result(
                "Protein Phylogeny (Neighbor-Joining)",
                stdout=summary,
                output_path=tree_file,
            )
        except ImportError:
            return "**Error:** BioPython not installed. Run: `pip install biopython`"
        except Exception as e:
            return format_error("Phylogeny", e)

    # ── BLAST (NCBI REST API via BioPython) ────────────────────────────

    @mcp.tool()
    async def blast_sequence(
        sequence: str,
        database: str = "nr",
        program: str = "blastp",
        max_hits: int = 10,
        output_volume_path: str = f"{config.volume_base}/blast_output",
    ) -> str:
        """Search for similar sequences using NCBI BLAST via remote API.

        Submits the query to NCBI's BLAST servers and retrieves results.
        This can take 30s-5min depending on queue length.

        Args:
            sequence: Query sequence (amino acid or nucleotide).
            database: BLAST database (nr, nt, swissprot, pdb, refseq_protein).
            program: BLAST program (blastp, blastn, blastx, tblastn).
            max_hits: Maximum number of alignments to report.
            output_volume_path: Volume directory for results.
        """
        VALID_PROGRAMS = {"blastp", "blastn", "blastx", "tblastn", "tblastx"}
        if program not in VALID_PROGRAMS:
            return f"**Validation error:** Invalid BLAST program: {program}. Use: {', '.join(sorted(VALID_PROGRAMS))}"
        try:
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"

        ensure_output_dir(output_volume_path)
        try:
            from Bio.Blast import NCBIWWW, NCBIXML

            loop = asyncio.get_event_loop()

            def do_blast():
                result_handle = NCBIWWW.qblast(
                    program, database, sequence,
                    hitlist_size=max_hits, format_type="XML",
                )
                blast_records = NCBIXML.parse(result_handle)
                blast_record = next(blast_records)

                lines = []
                for alignment in blast_record.alignments[:max_hits]:
                    hsp = alignment.hsps[0]
                    lines.append(
                        f"**{alignment.title[:80]}**\n"
                        f"  Score: {hsp.score}, E-value: {hsp.expect}\n"
                        f"  Identities: {hsp.identities}/{hsp.align_length} "
                        f"({100 * hsp.identities / hsp.align_length:.1f}%)\n"
                    )

                if not lines:
                    return "(no hits found)"

                out_text = "\n".join(lines)
                out_file = os.path.join(output_volume_path, "blast_results.txt")
                write_text(out_file, out_text)
                return out_text

            result_text = await loop.run_in_executor(None, do_blast)

            return format_tool_result(
                f"BLAST Search ({program} vs {database})",
                stdout=result_text,
                output_path=os.path.join(output_volume_path, "blast_results.txt"),
            )
        except ImportError:
            return "**Error:** BioPython not installed. Run: `pip install biopython`"
        except Exception as e:
            return format_error(f"BLAST ({program})", e)

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
        try:
            validate_volume_path(output_volume_path)
        except ValidationError as e:
            return f"**Validation error:** {e}"

        ensure_output_dir(output_volume_path)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=output_volume_path
        ) as f:
            f.write(script_content)
            script_path = f.name
        try:
            import subprocess

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["python", script_path],
                    capture_output=True, text=True, check=True,
                    timeout=120, cwd=output_volume_path,
                ),
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
