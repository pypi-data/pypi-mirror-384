"""Unit tests for the merge.py module using PyMuPDF."""

import tempfile
from pathlib import Path

import fitz  # PyMuPDF
import pytest

from pdf_pipeline.merge import merge_pdfs


@pytest.fixture
def temp_dir_with_pdfs() -> Path:
    """Create a temporary directory with a nested structure and dummy PDFs using PyMuPDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        def create_dummy_pdf(path: Path):
            with fitz.open() as doc:
                doc.new_page()
                doc.save(path)

        # Root level
        create_dummy_pdf(root / "root.pdf")

        # Subfolder A
        folder_a = root / "folderA"
        folder_a.mkdir()
        create_dummy_pdf(folder_a / "doc_a1.pdf")
        create_dummy_pdf(folder_a / "doc_a2.pdf")

        # Subfolder B with nested folder
        folder_b = root / "folderB"
        folder_b.mkdir()
        subfolder_b1 = folder_b / "subB1"
        subfolder_b1.mkdir()
        create_dummy_pdf(subfolder_b1 / "doc_b1.pdf")

        yield root


def test_merge_pdfs_creates_file(temp_dir_with_pdfs: Path):
    """Test that a merged PDF is created."""
    output_pdf = temp_dir_with_pdfs / "merged.pdf"
    merge_pdfs(temp_dir_with_pdfs, output_pdf)

    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0


def test_merge_pdfs_page_count(temp_dir_with_pdfs: Path):
    """Test that the merged PDF has the correct number of pages."""
    output_pdf = temp_dir_with_pdfs / "merged.pdf"
    merge_pdfs(temp_dir_with_pdfs, output_pdf)

    with fitz.open(output_pdf) as doc:
        # root.pdf, doc_a1.pdf, doc_a2.pdf, doc_b1.pdf
        assert doc.page_count == 4


def test_merge_pdfs_bookmarks(temp_dir_with_pdfs: Path):
    """Test the hierarchical structure of the bookmarks using PyMuPDF."""
    output_pdf = temp_dir_with_pdfs / "merged.pdf"
    merge_pdfs(temp_dir_with_pdfs, output_pdf)

    with fitz.open(output_pdf) as doc:
        toc = doc.get_toc()

        # Expected structure (order depends on sorted file iteration):
        # [1, 'folderA', 1], [2, 'doc_a1', 1], [2, 'doc_a2', 2],
        # [1, 'folderB', 3], [2, 'subB1', 3], [3, 'doc_b1', 3],
        # [1, 'root', 4]
        assert len(toc) == 7

        # Verify titles and levels
        expected_titles = {"folderA", "doc_a1", "doc_a2", "folderB", "subB1", "doc_b1", "root"}
        actual_titles = {item[1] for item in toc}
        assert actual_titles == expected_titles

        # Check a specific entry for correctness
        # Find the 'subB1' entry
        sub_b1_entry = next((item for item in toc if item[1] == "subB1"), None)
        assert sub_b1_entry is not None
        assert sub_b1_entry[0] == 2  # Level 2
        assert sub_b1_entry[2] == 3  # Page 3

        # Find the 'doc_b1' entry which should be a child of 'subB1'
        doc_b1_entry = next((item for item in toc if item[1] == "doc_b1"), None)
        assert doc_b1_entry is not None
        assert doc_b1_entry[0] == 3  # Level 3
        assert doc_b1_entry[2] == 3  # Page 3