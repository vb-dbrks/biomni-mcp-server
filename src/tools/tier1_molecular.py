"""Tier 1 tools — run directly in the App container via Python packages.

Tier 1 tools use /tmp for output since they run in the App container
and return results directly in the MCP response. No UC Volume needed.
"""

import asyncio
import logging
import os
import tempfile
import time

from mcp.server.fastmcp import FastMCP

from src.file_io import ensure_output_dir, write_text
from src.tool_wrapper import format_error, format_tool_result
from src.validation import ValidationError, validate_rna_sequence

logger = logging.getLogger("biomni.tier1")

# Tier 1 tools write to /tmp — results are returned inline, no Volume needed
TIER1_OUTPUT = "/tmp/biomni"


def register(mcp: FastMCP) -> None:
    # ── Ping (instant test) ────────────────────────────────────────────

    @mcp.tool()
    async def ping_biomni(message: str = "hello") -> str:
        """Simple ping to test the MCP server is responding. Returns the message back.

        Args:
            message: Any text to echo back.
        """
        print(f"=== PING called: {message} ===", flush=True)
        return f"Biomni MCP server is running. You said: {message}"

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
        t0 = time.monotonic()
        print(f"=== TOOL CALLED: predict_rna_secondary_structure seq={rna_sequence[:20]}... ===", flush=True)
        logger.info("predict_rna_secondary_structure called: seq=%s... temp=%s", rna_sequence[:20], temperature)

        try:
            rna_sequence = validate_rna_sequence(rna_sequence)
            logger.info("Validation passed (%.3fs)", time.monotonic() - t0)
        except ValidationError as e:
            logger.warning("Validation failed: %s", e)
            return f"**Validation error:** {e}"

        try:
            logger.info("Importing RNA module...")
            t1 = time.monotonic()
            import RNA
            logger.info("RNA imported (%.3fs)", time.monotonic() - t1)

            t2 = time.monotonic()
            md = RNA.md()
            md.temperature = temperature
            fc = RNA.fold_compound(rna_sequence, md)
            structure, mfe = fc.mfe()
            logger.info("MFE computed (%.3fs): %s %.2f", time.monotonic() - t2, structure, mfe)

            t3 = time.monotonic()
            fc.pf()
            centroid_struct, centroid_dist = fc.centroid()
            logger.info("Centroid computed (%.3fs)", time.monotonic() - t3)

            result_text = (
                f"Sequence:    {rna_sequence}\n"
                f"Structure:   {structure}\n"
                f"MFE:         {mfe:.2f} kcal/mol\n"
                f"Centroid:    {centroid_struct}\n"
                f"Distance:    {centroid_dist:.2f}\n"
                f"Temperature: {temperature} C\n"
                f"Length:      {len(rna_sequence)} nt"
            )

            logger.info("Tool completed successfully (%.3fs total)", time.monotonic() - t0)
            return format_tool_result(
                "RNA Structure Prediction (ViennaRNA)",
                stdout=result_text,
            )
        except ImportError as e:
            logger.error("ViennaRNA import failed: %s", e)
            return "**Error:** ViennaRNA Python package not installed. Run: `pip install ViennaRNA`"
        except Exception as e:
            logger.error("ViennaRNA error (%.3fs): %s", time.monotonic() - t0, e, exc_info=True)
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

    # ── BLAST (async: submit + poll) ─────────────────────────────────────

    import threading
    _blast_results: dict[str, dict] = {}
    _blast_counter = 0
    _blast_lock = threading.Lock()

    @mcp.tool()
    async def blast_sequence(
        sequence: str,
        database: str = "swissprot",
        program: str = "blastp",
        max_hits: int = 5,
    ) -> str:
        """Submit a BLAST search against NCBI. Returns a job ID immediately.

        NCBI BLAST takes 30-90 seconds. This tool submits the search and
        returns a job ID. Use check_blast_result with the job ID to get results.

        Args:
            sequence: Query sequence (amino acid or nucleotide).
            database: BLAST database — swissprot (fast), pdb, nr (slow), refseq_protein.
            program: BLAST program (blastp, blastn, blastx, tblastn).
            max_hits: Maximum number of alignments to report (default 5).
        """
        nonlocal _blast_counter
        VALID_PROGRAMS = {"blastp", "blastn", "blastx", "tblastn", "tblastx"}
        if program not in VALID_PROGRAMS:
            return f"**Error:** Invalid program: {program}. Use: {', '.join(sorted(VALID_PROGRAMS))}"

        with _blast_lock:
            _blast_counter += 1
            job_id = f"blast-{_blast_counter}"

        _blast_results[job_id] = {"status": "running", "result": None}

        def run_blast():
            try:
                from Bio.Blast import NCBIWWW, NCBIXML

                result_handle = NCBIWWW.qblast(
                    program, database, sequence,
                    hitlist_size=max_hits, format_type="XML",
                )
                blast_records = NCBIXML.parse(result_handle)
                blast_record = next(blast_records)

                lines = []
                for alignment in blast_record.alignments[:max_hits]:
                    hsp = alignment.hsps[0]
                    pct = 100 * hsp.identities / hsp.align_length if hsp.align_length else 0
                    lines.append(
                        f"**{alignment.title[:80]}**\n"
                        f"  Score: {hsp.score}, E-value: {hsp.expect}\n"
                        f"  Identities: {hsp.identities}/{hsp.align_length} ({pct:.1f}%)\n"
                    )

                text = "\n".join(lines) if lines else "(no hits found)"
                _blast_results[job_id] = {"status": "complete", "result": text}
            except Exception as e:
                _blast_results[job_id] = {"status": "error", "result": str(e)}

        thread = threading.Thread(target=run_blast, daemon=True)
        thread.start()

        return (
            f"## BLAST Search Submitted\n\n"
            f"- **Job ID:** {job_id}\n"
            f"- **Program:** {program}\n"
            f"- **Database:** {database}\n"
            f"- **Sequence:** {sequence[:30]}...\n\n"
            f"NCBI BLAST typically takes 30-90 seconds.\n"
            f"Use `check_blast_result(job_id='{job_id}')` to get results."
        )

    @mcp.tool()
    async def check_blast_result(job_id: str) -> str:
        """Check the result of a previously submitted BLAST search.

        Args:
            job_id: The job ID returned by blast_sequence.
        """
        if job_id not in _blast_results:
            return f"**Error:** Unknown job ID: {job_id}"

        entry = _blast_results[job_id]
        if entry["status"] == "running":
            return f"BLAST search **{job_id}** is still running. Try again in 30 seconds."
        elif entry["status"] == "error":
            return f"BLAST search **{job_id}** failed: {entry['result']}"
        else:
            return format_tool_result(
                f"BLAST Search Results ({job_id})",
                stdout=entry["result"],
            )

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
