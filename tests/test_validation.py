"""Tests for input validation."""

import pytest

from src.validation import (
    ValidationError,
    validate_genome,
    validate_rna_sequence,
    validate_smiles,
    validate_volume_path,
)


class TestRnaValidation:
    def test_valid_rna(self):
        assert validate_rna_sequence("ACGU") == "ACGU"

    def test_lowercase_normalized(self):
        assert validate_rna_sequence("acgu") == "ACGU"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_rna_sequence("")

    def test_invalid_chars(self):
        with pytest.raises(ValidationError, match="Invalid RNA"):
            validate_rna_sequence("ACGTX")

    def test_dna_t_rejected(self):
        with pytest.raises(ValidationError, match="T"):
            validate_rna_sequence("ACGT")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="too long"):
            validate_rna_sequence("A" * 10_001)


class TestSmilesValidation:
    def test_valid_aspirin(self):
        assert validate_smiles("CC(=O)Oc1ccccc1C(=O)O") == "CC(=O)Oc1ccccc1C(=O)O"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_smiles("")

    def test_invalid_chars(self):
        with pytest.raises(ValidationError, match="Invalid SMILES"):
            validate_smiles("CC(=O) invalid spaces")


class TestVolumePathValidation:
    def test_valid_path(self):
        assert validate_volume_path("/Volumes/cat/schema/vol") == "/Volumes/cat/schema/vol"

    def test_non_volume_path(self):
        with pytest.raises(ValidationError, match="/Volumes/"):
            validate_volume_path("/tmp/data")

    def test_path_traversal(self):
        with pytest.raises(ValidationError, match="traversal"):
            validate_volume_path("/Volumes/cat/../../../etc/passwd")

    def test_must_exist(self, tmp_path):
        with pytest.raises(ValidationError, match="does not exist"):
            validate_volume_path("/Volumes/nonexistent", must_exist=True)


class TestGenomeValidation:
    def test_valid_genomes(self):
        for g in ["hg38", "hg19", "mm10"]:
            assert validate_genome(g) == g

    def test_unknown_genome(self):
        with pytest.raises(ValidationError, match="Unknown genome"):
            validate_genome("potato")
