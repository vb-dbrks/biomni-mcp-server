"""Tier 1 tools — run directly in the App container via Python packages.

Tier 1 tools use /tmp for output since they run in the App container
and return results directly in the MCP response. No UC Volume needed.
"""

import asyncio
import os
import tempfile

from mcp.server.fastmcp import FastMCP

from src.file_io import ensure_output_dir, write_text
from src.tool_wrapper import format_error, format_tool_result
from src.validation import ValidationError, validate_rna_sequence

# Tier 1 tools write to /tmp — results are returned inline, no Volume needed
TIER1_OUTPUT = "/tmp/biomni"


def register(mcp: FastMCP) -> None:
    # ── ViennaRNA ──────────────────────────────────────────────────────

    @mcp.tool()
    async def predict_rna_secondary_structure(
        rna_sequence: str,
        temperature: float = 37.0,
    ) -> str:
        """Predict RNA secondary structure and minimum free energy using ViennaRNA.

        Args:
            rna_sequence: RNA sequence string (ACGU characters, max 10000).
            temperature: Folding temperature in Celsius (default 37.0).
        """
        try:
            rna_sequence = validate_rna_sequence(rna_sequence)
        except ValidationError as e:
            return f"**Validation error:** {e}"

        try:
            import RNA

            md = RNA.md()
            md.temperature = temperature
            fc = RNA.fold_compound(rna_sequence, md)
            structure, mfe = fc.mfe()

            fc.pf()
            centroid_struct, centroid_dist = fc.centroid()

            result_text = (
                f"Sequence:    {rna_sequence}\n"
                f"Structure:   {structure}\n"
                f"MFE:         {mfe:.2f} kcal/mol\n"
                f"Centroid:    {centroid_struct}\n"
                f"Distance:    {centroid_dist:.2f}\n"
                f"Temperature: {temperature} C\n"
                f"Length:      {len(rna_sequence)} nt"
            )

            return format_tool_result(
                "RNA Structure Prediction (ViennaRNA)",
                stdout=result_text,
            )
        except ImportError:
            return "**Error:** ViennaRNA Python package not installed. Run: `pip install ViennaRNA`"
        except Exception as e:
            return format_error("ViennaRNA RNAfold", e)

    # ── pLannotate ─────────────────────────────────────────────────────

    @mcp.tool()
    async def annotate_plasmid(
        sequence_file: str,
    ) -> str:
        """Annotate a plasmid DNA sequence using pLannotate.

        Args:
            sequence_file: Path to a FASTA/GenBank file.
        """
        if not os.path.isfile(sequence_file):
            return f"**Error:** File not found: {sequence_file}"

        output_dir = os.path.join(TIER1_OUTPUT, "plannotate")
        ensure_output_dir(output_dir)
        try:
            import subprocess

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["plannotate", "batch", "-i", sequence_file, "-o", output_dir],
                    capture_output=True, text=True, check=True, timeout=300,
                ),
            )
            return format_tool_result(
                "Plasmid Annotation (pLannotate)",
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except Exception as e:
            return format_error("pLannotate", e)

    # ── MUSCLE (alignment via BioPython) ───────────────────────────────

    @mcp.tool()
    async def analyze_protein_conservation(
        fasta_file: str,
    ) -> str:
        """Perform multiple sequence alignment to analyze protein conservation.

        Args:
            fasta_file: Path to a multi-FASTA file.
        """
        if not os.path.isfile(fasta_file):
            return f"**Error:** File not found: {fasta_file}"

        try:
            from Bio import SeqIO
            from Bio.Align import PairwiseAligner

            loop = asyncio.get_event_loop()

            def do_alignment():
                records = list(SeqIO.parse(fasta_file, "fasta"))
                if len(records) < 2:
                    return "Need at least 2 sequences for alignment."

                aligner = PairwiseAligner()
                aligner.mode = "global"

                summary = (
                    f"Sequences: {len(records)}\n"
                    f"IDs: {', '.join(r.id for r in records[:10])}"
                )
                if len(records) > 10:
                    summary += f"\n... and {len(records) - 10} more"

                # Show pairwise scores for first few pairs
                if len(records) >= 2:
                    score = aligner.score(records[0].seq, records[1].seq)
                    summary += f"\nPairwise score ({records[0].id} vs {records[1].id}): {score:.1f}"

                return summary

            summary = await loop.run_in_executor(None, do_alignment)

            return format_tool_result(
                "Protein Conservation (Sequence Alignment)",
                stdout=summary,
            )
        except ImportError:
            return "**Error:** BioPython not installed. Run: `pip install biopython`"
        except Exception as e:
            return format_error("Sequence Alignment", e)

    # ── Protein Phylogeny ──────────────────────────────────────────────

    @mcp.tool()
    async def analyze_protein_phylogeny(
        fasta_file: str,
    ) -> str:
        """Build a distance-based phylogenetic tree from protein sequences.

        Args:
            fasta_file: Path to a multi-FASTA file.
        """
        if not os.path.isfile(fasta_file):
            return f"**Error:** File not found: {fasta_file}"

        try:
            from Bio import SeqIO, Phylo
            from Bio.Phylo.TreeConstruction import (
                DistanceCalculator,
                DistanceTreeConstructor,
            )
            from Bio.Align import MultipleSeqAlignment
            import io

            loop = asyncio.get_event_loop()

            def do_phylogeny():
                records = list(SeqIO.parse(fasta_file, "fasta"))
                if len(records) < 3:
                    return "Need at least 3 sequences for phylogenetic tree."

                alignment = MultipleSeqAlignment(records)
                calculator = DistanceCalculator("identity")
                dm = calculator.get_distance(alignment)
                constructor = DistanceTreeConstructor(calculator, "nj")
                tree = constructor.nj(dm)

                # Render tree as text
                buf = io.StringIO()
                Phylo.draw_ascii(tree, file=buf)
                tree_text = buf.getvalue()

                # Also get newick format
                nwk_buf = io.StringIO()
                Phylo.write(tree, nwk_buf, "newick")

                return (
                    f"Sequences: {len(records)}\n"
                    f"Method: Neighbor-Joining (identity distance)\n\n"
                    f"Tree (ASCII):\n```\n{tree_text}```\n\n"
                    f"Newick: `{nwk_buf.getvalue().strip()}`"
                )

            result = await loop.run_in_executor(None, do_phylogeny)

            return format_tool_result(
                "Protein Phylogeny (Neighbor-Joining)",
                stdout=result,
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
    ) -> str:
        """Search for similar sequences using NCBI BLAST via remote API.

        Submits the query to NCBI's BLAST servers. Takes 30s-5min.

        Args:
            sequence: Query sequence (amino acid or nucleotide).
            database: BLAST database (nr, nt, swissprot, pdb, refseq_protein).
            program: BLAST program (blastp, blastn, blastx, tblastn).
            max_hits: Maximum number of alignments to report.
        """
        VALID_PROGRAMS = {"blastp", "blastn", "blastx", "tblastn", "tblastx"}
        if program not in VALID_PROGRAMS:
            return f"**Error:** Invalid program: {program}. Use: {', '.join(sorted(VALID_PROGRAMS))}"

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

                return "\n".join(lines) if lines else "(no hits found)"

            result_text = await loop.run_in_executor(None, do_blast)

            return format_tool_result(
                f"BLAST Search ({program} vs {database})",
                stdout=result_text,
            )
        except ImportError:
            return "**Error:** BioPython not installed. Run: `pip install biopython`"
        except Exception as e:
            return format_error(f"BLAST ({program})", e)

    # ── PyLabRobot ─────────────────────────────────────────────────────

    @mcp.tool()
    async def test_pylabrobot_script(
        script_content: str,
    ) -> str:
        """Test a PyLabRobot automation script in simulation mode.

        Args:
            script_content: Python source code using PyLabRobot APIs.
        """
        work_dir = os.path.join(TIER1_OUTPUT, "pylabrobot")
        ensure_output_dir(work_dir)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=work_dir
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
                    timeout=120, cwd=work_dir,
                ),
            )
            return format_tool_result(
                "PyLabRobot Simulation",
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except Exception as e:
            return format_error("PyLabRobot", e)
        finally:
            os.unlink(script_path)
