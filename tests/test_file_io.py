"""Tests for file I/O helpers."""

import os

from src.file_io import ensure_output_dir, list_files, read_file_head, write_text


def test_list_files_empty(tmp_path):
    entries = list_files(str(tmp_path))
    assert entries == []


def test_list_files_with_content(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    entries = list_files(str(tmp_path))
    assert len(entries) == 2
    names = {e["name"] for e in entries}
    assert names == {"a.txt", "subdir"}


def test_list_files_nonexistent():
    entries = list_files("/nonexistent/path")
    assert entries == []


def test_read_file_head(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("\n".join(f"line {i}" for i in range(100)))
    content = read_file_head(str(f), max_lines=5)
    assert "line 0" in content
    assert "line 4" in content
    assert "line 5" not in content


def test_write_text(tmp_path):
    path = str(tmp_path / "sub" / "out.txt")
    result = write_text(path, "test content")
    assert result == path
    assert os.path.isfile(path)
    with open(path) as f:
        assert f.read() == "test content"


def test_ensure_output_dir(tmp_path):
    path = str(tmp_path / "new" / "dir")
    ensure_output_dir(path)
    assert os.path.isdir(path)
