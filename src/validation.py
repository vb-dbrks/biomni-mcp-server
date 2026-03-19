"""Input validation for bioinformatics tool parameters."""

import os
import re

# Valid characters for nucleotide/protein sequences
RNA_CHARS = set("ACGUacgu")
DNA_CHARS = set("ACGTNacgtn")
PROTEIN_CHARS = set("ACDEFGHIKLMNPQRSTVWYXacdefghiklmnpqrstvwyx*-")
SMILES_PATTERN = re.compile(r"^[A-Za-z0-9@+\-\[\]\(\)\\/%=#$.,~!:]+$")


class ValidationError(Exception):
    """Raised when tool input validation fails."""
    pass


def validate_rna_sequence(seq: str) -> str:
    """Validate and normalize an RNA sequence."""
    seq = seq.strip().upper()
    if not seq:
        raise ValidationError("RNA sequence is empty.")
    if len(seq) > 10_000:
        raise ValidationError(f"RNA sequence too long ({len(seq)} chars, max 10000).")
    invalid = set(seq) - RNA_CHARS
    if invalid:
        raise ValidationError(
            f"Invalid RNA characters: {', '.join(sorted(invalid))}. "
            "Expected only A, C, G, U."
        )
    return seq


def validate_protein_sequence(seq: str) -> str:
    """Validate and normalize a protein sequence."""
    seq = seq.strip().upper()
    if not seq:
        raise ValidationError("Protein sequence is empty.")
    invalid = set(seq) - PROTEIN_CHARS
    if invalid:
        raise ValidationError(
            f"Invalid protein characters: {', '.join(sorted(invalid))}."
        )
    return seq


def validate_smiles(smiles: str) -> str:
    """Basic validation of a SMILES string."""
    smiles = smiles.strip()
    if not smiles:
        raise ValidationError("SMILES string is empty.")
    if not SMILES_PATTERN.match(smiles):
        raise ValidationError("Invalid SMILES string format.")
    return smiles


def validate_volume_path(path: str, must_exist: bool = False) -> str:
    """Validate a Unity Catalog Volume path."""
    if not path.startswith("/Volumes/"):
        raise ValidationError(
            f"Path must start with /Volumes/. Got: {path}"
        )
    if ".." in path:
        raise ValidationError("Path traversal (..) not allowed.")
    if must_exist and not os.path.exists(path):
        raise ValidationError(f"Path does not exist: {path}")
    return path


def validate_volume_file(path: str) -> str:
    """Validate that a Volume file path exists and is a file."""
    validate_volume_path(path)
    if not os.path.isfile(path):
        raise ValidationError(f"File not found: {path}")
    return path


def validate_genome(genome: str) -> str:
    """Validate a reference genome name."""
    allowed = {"hg38", "hg19", "mm10", "mm39", "ce11", "dm6", "sacCer3"}
    if genome not in allowed:
        raise ValidationError(
            f"Unknown genome: {genome}. Supported: {', '.join(sorted(allowed))}"
        )
    return genome
