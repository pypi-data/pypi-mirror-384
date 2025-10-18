"""Unit tests for the convert.py module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from pdf_pipeline.convert import (
    convert_image_to_pdf,
    convert_office_to_pdf,
    run_ocr,
)


@pytest.fixture
def temp_paths():
    """Provide a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_convert_image_to_pdf(temp_paths: Path):
    """Test that an image is correctly converted to a PDF."""
    image_path = temp_paths / "test.png"
    pdf_path = temp_paths / "test.pdf"

    Image.new("RGB", (100, 100), color="red").save(image_path)

    convert_image_to_pdf(image_path, pdf_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


@patch("pdf_pipeline.convert.check_command_exists", return_value=True)
@patch("subprocess.run")
def test_convert_office_to_pdf_success(mock_subprocess_run, mock_check_command, temp_paths: Path):
    """Test office conversion when LibreOffice is present and succeeds."""
    doc_path = temp_paths / "test.docx"
    doc_path.touch()

    def create_pdf(*args, **kwargs):
        output_dir = Path(args[0][5])
        (output_dir / "test.pdf").touch()
        return MagicMock(check=MagicMock(), stderr="")

    mock_subprocess_run.side_effect = create_pdf

    result_path = convert_office_to_pdf(doc_path, temp_paths)

    mock_check_command.assert_called_once_with("libreoffice")
    assert mock_subprocess_run.called
    assert result_path is not None
    assert result_path.name == "test.pdf"
    assert result_path.exists()


@patch("pdf_pipeline.convert.check_command_exists", return_value=False)
def test_convert_office_to_pdf_no_libreoffice(mock_check_command, temp_paths: Path):
    """Test that office conversion is skipped if LibreOffice is not found."""
    doc_path = temp_paths / "test.docx"
    doc_path.touch()

    result_path = convert_office_to_pdf(doc_path, temp_paths)

    mock_check_command.assert_called_once_with("libreoffice")
    assert result_path is None


@patch("pdf_pipeline.convert.ocrmypdf.ocr")
def test_run_ocr_success(mock_ocrmypdf_ocr, temp_paths: Path):
    """Test that ocrmypdf.ocr is called with the correct parameters."""
    input_pdf = temp_paths / "input.pdf"
    output_pdf = temp_paths / "output.pdf"
    input_pdf.touch()

    run_ocr(input_pdf, output_pdf, "eng", force_ocr=True, skip_text=False)

    mock_ocrmypdf_ocr.assert_called_once_with(
        input_file=input_pdf,
        output_file=output_pdf,
        language="eng",
        force_ocr=True,
        skip_text=False,
        clean=True,
        output_type='pdf',
        skip_big=10,
        tesseract_timeout=25,
        optimize=0,
        progress_bar=False,
    )

@patch("pdf_pipeline.convert.ocrmypdf.ocr")
def test_run_ocr_skip_text(mock_ocrmypdf_ocr, temp_paths: Path):
    """Test that skip_text is correctly set to True when force_ocr is False."""
    input_pdf = temp_paths / "input.pdf"
    output_pdf = temp_paths / "output.pdf"
    input_pdf.touch()

    run_ocr(input_pdf, output_pdf, "fra", force_ocr=False, skip_text=True)

    mock_ocrmypdf_ocr.assert_called_once_with(
        input_file=input_pdf,
        output_file=output_pdf,
        language="fra",
        force_ocr=False,
        skip_text=True,
        clean=True,
        output_type='pdf',
        skip_big=10,
        tesseract_timeout=25,
        optimize=0,
        progress_bar=False,
    )
