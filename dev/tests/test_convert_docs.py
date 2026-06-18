"""Tests for convert_docs.py"""

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def converter(tmp_project, aienv_dir):
    with patch("convert_docs.MarkItDown"):
        from convert_docs import DocConverter
        return DocConverter(tmp_project, aienv_dir)


@pytest.fixture
def sample_docx(tmp_path):
    """Minimal real file for hash testing."""
    f = tmp_path / "sample.docx"
    f.write_bytes(b"fake docx content")
    return f


# ── Hash / state ──────────────────────────────────────────────────────────────

def test_skip_unchanged_file(converter, sample_docx, capsys):
    """File with same hash should be skipped on second convert."""
    mock_result = MagicMock()
    mock_result.text_content = "# Hello\nWorld"
    converter.md.convert.return_value = mock_result

    converter.convert(sample_docx)
    converter.convert(sample_docx)  # second call

    captured = capsys.readouterr()
    assert "[skip]" in captured.out
    assert "unchanged" in captured.out


def test_reconvert_on_file_change(converter, sample_docx, capsys):
    """Modified file (different hash) should be reconverted."""
    mock_result = MagicMock()
    mock_result.text_content = "# Hello"
    converter.md.convert.return_value = mock_result

    converter.convert(sample_docx)
    sample_docx.write_bytes(b"updated content")
    converter.convert(sample_docx)

    captured = capsys.readouterr()
    assert captured.out.count("[convert]") == 2


def test_state_file_created(converter, sample_docx):
    """State JSON must be written after conversion."""
    mock_result = MagicMock()
    mock_result.text_content = "# Doc"
    converter.md.convert.return_value = mock_result

    converter.convert(sample_docx)

    assert converter.state_path.exists()
    state = json.loads(converter.state_path.read_text())
    assert str(sample_docx) in state["files"]


def test_state_records_hash(converter, sample_docx):
    """State must include correct sha256 hash."""
    import hashlib
    mock_result = MagicMock()
    mock_result.text_content = "content"
    converter.md.convert.return_value = mock_result

    converter.convert(sample_docx)

    expected = hashlib.sha256(sample_docx.read_bytes()).hexdigest()
    state = json.loads(converter.state_path.read_text())
    assert state["files"][str(sample_docx)]["hash"] == expected


def test_unsupported_extension_skipped(converter, tmp_path, capsys):
    """Files with unsupported extensions should be skipped."""
    f = tmp_path / "file.xyz"
    f.write_text("data")
    converter.convert(f)
    assert "[skip]" in capsys.readouterr().out


# ── Image extraction ──────────────────────────────────────────────────────────

def test_image_extracted_to_file(converter, tmp_project):
    """Base64 data URI in markdown should become a saved image file."""
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    b64 = base64.b64encode(png_bytes).decode()
    text = f"![alt](data:image/png;base64,{b64})"

    result = converter._extract_images(text, tmp_project / "md-doc" / "doc", "doc")

    assert "data:image/png;base64," not in result
    assert "![alt](" in result
    saved = list((tmp_project / "md-doc" / "doc").glob("*.png"))
    assert len(saved) == 1
    assert saved[0].read_bytes() == png_bytes


def test_multiple_images_numbered(converter, tmp_project):
    """Multiple images should get sequential filenames."""
    png = b"\x89PNG" + b"\x00" * 10
    b64 = base64.b64encode(png).decode()
    text = f"![a](data:image/png;base64,{b64})\n![b](data:image/png;base64,{b64})"

    converter._extract_images(text, tmp_project / "md-doc" / "doc", "doc")

    files = sorted((tmp_project / "md-doc" / "doc").glob("*.png"))
    assert len(files) == 2
    assert files[0].name == "doc_001.png"
    assert files[1].name == "doc_002.png"


# ── Chunking — chapter ────────────────────────────────────────────────────────

def test_chunk_by_chapter_splits_on_headings(converter):
    text = "# Chapter 1\ncontent\n# Chapter 2\nmore"
    chunks = converter._chunk_by_chapter(text)
    assert len(chunks) == 2
    assert "Chapter 1" in chunks[0]
    assert "Chapter 2" in chunks[1]


def test_chunk_by_chapter_returns_empty_if_no_headings(converter):
    text = "Just plain text without any headings here."
    assert converter._chunk_by_chapter(text) == []


def test_chunk_h2_headings(converter):
    text = "## Section A\ncontent\n## Section B\nmore"
    chunks = converter._chunk_by_chapter(text)
    assert len(chunks) == 2


# ── Chunking — size ───────────────────────────────────────────────────────────

def test_chunk_by_size_respects_limit(converter):
    from convert_docs import CHUNK_SIZE
    text = "x" * (CHUNK_SIZE * 3)
    chunks = converter._chunk_by_size(text)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert len(chunk.encode("utf-8")) <= CHUNK_SIZE + 200  # small margin for newline


def test_chunk_by_size_prefers_newline_break(converter):
    """Chunks should break at newlines when possible."""
    line = "word " * 100 + "\n"
    text = line * 50
    chunks = converter._chunk_by_size(text)
    for chunk in chunks[:-1]:
        assert chunk.endswith("\n")


# ── Chunking — merge/split ────────────────────────────────────────────────────

def test_merge_small_chapters(converter):
    """Small chapters should be merged to reduce chunk count."""
    from convert_docs import CHUNK_SIZE
    small = "# Ch\n" + "x" * 100
    chunks = [small] * 10
    merged = converter._merge_or_split(chunks)
    assert len(merged) < 10


def test_large_chapter_further_split(converter):
    """A single chapter bigger than CHUNK_SIZE must be split."""
    from convert_docs import CHUNK_SIZE
    big_chapter = "# Big\n" + "x\n" * (CHUNK_SIZE // 2)
    result = converter._merge_or_split([big_chapter])
    total = sum(len(c.encode()) for c in result)
    assert total >= len(big_chapter.encode()) - 10
    for chunk in result:
        assert len(chunk.encode()) <= CHUNK_SIZE + 200


# ── Output files ──────────────────────────────────────────────────────────────

def test_output_written_to_md_doc(converter, sample_docx):
    mock_result = MagicMock()
    mock_result.text_content = "# Hello\nSmall content"
    converter.md.convert.return_value = mock_result

    converter.convert(sample_docx)

    assert (converter.output_dir / "sample.md").exists()


def test_chunked_output_numbered(converter, sample_docx):
    from convert_docs import CHUNK_SIZE
    mock_result = MagicMock()
    mock_result.text_content = "# Ch1\n" + "x\n" * CHUNK_SIZE + "\n# Ch2\n" + "y\n" * CHUNK_SIZE
    converter.md.convert.return_value = mock_result

    converter.convert(sample_docx)

    parts = list(converter.output_dir.glob("sample_part*.md"))
    assert len(parts) >= 2
