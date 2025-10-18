"""
Core module for converting various document types to OCR-ed PDFs.

This module orchestrates the process of:
1. Scanning an input directory for supported files (images, office docs, archives).
2. Extracting archives into temporary directories.
3. Converting non-PDF files (images, office documents) into PDFs.
4. Applying OCR to each PDF using the ocrmypdf library.
"""

import logging
import subprocess
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Callable, Optional

import shutil

import ocrmypdf
import img2pdf
from rich.progress import Progress

from . import utils
from .utils import (
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_OFFICE_EXTENSIONS,
    SUPPORTED_ARCHIVE_EXTENSIONS,
    SUPPORTED_PDF_EXTENSION,
    check_command_exists,
)

log = logging.getLogger(__name__)


def convert_image_to_pdf(image_path: Path, pdf_path: Path) -> None:
    """Convert a single image file to a one-page PDF using img2pdf."""
    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(str(image_path)))  # type: ignore
        log.debug(f"Converted image {image_path.name} to PDF using img2pdf.")
    except Exception as e:
        log.error(f"Failed to convert image {image_path.name} with img2pdf: {e}")


def convert_office_to_pdf(doc_path: Path, output_dir: Path) -> Optional[Path]:
    """Convert an office document to PDF using LibreOffice."""
    if not check_command_exists("libreoffice"):
        log.warning(
            "LibreOffice not found. Skipping conversion of office documents."
        )
        return None

    try:
        log.debug(f"Converting office document: {doc_path.name}")
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(doc_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        pdf_path = output_dir / f"{doc_path.stem}.pdf"
        if pdf_path.exists():
            log.debug(f"Successfully converted {doc_path.name} to {pdf_path.name}")
            return pdf_path
        else:
            log.error(f"LibreOffice conversion failed for {doc_path.name}, no output PDF.")
            return None
    except subprocess.CalledProcessError as e:
        log.error(f"Error converting {doc_path.name} with LibreOffice: {e.stderr}")
        return None
    except FileNotFoundError:
        log.error(
            f"Could not find 'libreoffice' command to convert {doc_path.name}. Please ensure it is installed and in your PATH."
        )
        return None

def run_ocr(
    input_file: Path,
    output_file: Path,
    lang: str = "fra",
    force_ocr: bool = False,
    skip_text: bool = True,
    optimize: int = 0,
) -> None:
    """Run OCR on a PDF file."""
    try:
        utils.set_log_context(input_file.name)
        try:
            log.info(f"Processing OCR for {input_file.name}...")

            log.debug(f"Running ocrmypdf with options: {{'input_file': '{input_file}', 'output_file': '{output_file}', 'language': '{lang}', 'force_ocr': {force_ocr}, 'skip_text': {skip_text}, 'optimize': {optimize}}})")

            ocr_options = {
                "input_file": input_file,
                "output_file": output_file,
                "language": lang,
                "force_ocr": force_ocr,
                "skip_text": skip_text,
                "clean": True,
                "output_type": "pdf",
                "skip_big": 10,
                "tesseract_timeout": 25,
                "optimize": optimize,
                "progress_bar": False,
            }

            if optimize > 0:
                ocr_options["jbig2"] = False
                ocr_options["jpeg_quality"] = 75

            result = ocrmypdf.ocr(**ocr_options)  # type: ignore
            log.info(result)
            log.debug(f"OCR complete for {input_file.name}. Output: {output_file.name}")
        except ocrmypdf.exceptions.EncryptedPdfError: # type: ignore
            log.info(f"Skipping encrypted PDF: {input_file.name}")
        except ocrmypdf.exceptions.PriorOcrFoundError: # type: ignore
            log.info(f"Skipping {input_file.name}, OCR text already present.")
        except ocrmypdf.exceptions.DigitalSignatureError: # type: ignore
            log.info("Skipped {input_file.name} because it has a digital signature")
        except ocrmypdf.exceptions.TaggedPDFError: # type: ignore
            log.info(
                    "Skipped {input_file.name} because it does not need ocr as it is tagged"
                )        
        except Exception as e:
            log.warning(f"An unexpected error occurred during OCR for {input_file.name}: {e}")
            log.warning(f"Copying original file {input_file.name} to output as a fallback.")
            try:
                shutil.copy(input_file, output_file)
            except Exception as copy_e:
                log.error(f"Failed to copy {input_file.name} to {output_file.name}: {copy_e}")
    finally:
        utils.clear_log_context()

def process_folder(
    input_dir: Path,
    output_dir: Path,
    lang: str,
    force_ocr: bool = False,
    skip_text: bool = True,
    convert_office: bool = True,
    optimize: int = 0,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Main orchestration function to convert and OCR a folder."""
    output_dir.mkdir(exist_ok=True)

    file_generators = [
        input_dir.rglob(f"*{ext}") for ext in SUPPORTED_IMAGE_EXTENSIONS
    ]
    if convert_office:
        file_generators.extend(
            [input_dir.rglob(f"*{ext}") for ext in SUPPORTED_OFFICE_EXTENSIONS]
        )
    file_generators.extend(
        [input_dir.rglob(f"*{ext}") for ext in SUPPORTED_ARCHIVE_EXTENSIONS]
    )
    file_generators.append(input_dir.rglob(f"*{SUPPORTED_PDF_EXTENSION}"))

    all_files = {path for gen in file_generators for path in gen if path.is_file()}

    total_pages = utils.count_pages(all_files)
    log.info(f"Estimated total pages to be processed: {total_pages}")

    with Progress() as progress:
        total_files = len(all_files)
        task = progress.add_task("[cyan]Converting & OCRing...", total=total_files)

        try:
            for i, path in enumerate(all_files):
                if stop_event and stop_event.is_set():
                    log.info("Stopping process as requested by user.")
                    break
                log.debug(f"Processing input path: {path}")

                output_subdir = output_dir / path.relative_to(input_dir).parent
                ext = path.suffix.lower()

                expected_output_path = None
                if ext in SUPPORTED_IMAGE_EXTENSIONS:
                    expected_output_path = output_subdir / f"{path.stem}.pdf"
                elif ext in SUPPORTED_OFFICE_EXTENSIONS and convert_office:
                    expected_output_path = output_subdir / f"{path.stem}.pdf"
                elif ext == SUPPORTED_PDF_EXTENSION:
                    expected_output_path = output_subdir / path.name

                if expected_output_path and expected_output_path.exists():
                    log.info(f"Skipping already processed file: {path.name}")
                    progress.update(task, advance=1, description=f"Skipped {path.name}")
                    if progress_callback:
                        progress_callback(i + 1, total_files)
                    continue

                progress.update(task, advance=1, description=f"Processing {path.name}")
                if progress_callback:
                    progress_callback(i + 1, total_files)

                if not path.is_file():
                    log.debug(f"Skipping non-file entry: {path}")
                    continue

                output_subdir = output_dir / path.relative_to(input_dir).parent
                output_subdir.mkdir(parents=True, exist_ok=True)
                log.debug(f"Output subdirectory for {path.name}: {output_subdir}")

                ext = path.suffix.lower()
                temp_pdf_path = None

                try:
                    if ext in SUPPORTED_IMAGE_EXTENSIONS:
                        log.debug(f"Converting image {path.name} to PDF.")
                        temp_pdf_path = output_subdir / f"_temp_{path.stem}.pdf"
                        convert_image_to_pdf(path, temp_pdf_path)
                        run_ocr(temp_pdf_path, output_subdir / f"{path.stem}.pdf", lang, force_ocr, skip_text, optimize)

                    elif ext in SUPPORTED_OFFICE_EXTENSIONS and convert_office:
                        log.debug(f"Converting office document {path.name} to PDF.")
                        pdf_path = convert_office_to_pdf(path, output_subdir)
                        if pdf_path:
                            run_ocr(pdf_path, pdf_path, lang, force_ocr, skip_text, optimize)

                    elif ext == SUPPORTED_PDF_EXTENSION:
                        log.debug(f"Processing existing PDF {path.name}.")
                        run_ocr(path, output_subdir / path.name, lang, force_ocr, skip_text, optimize)

                    elif ext in SUPPORTED_ARCHIVE_EXTENSIONS:
                        log.debug(f"Handling archive {path.name}.")
                        with tempfile.TemporaryDirectory() as temp_archive_dir:
                            log.info(f"Extracting archive: {path.name}")
                            try:
                                with zipfile.ZipFile(path, 'r') as zip_ref:
                                    zip_ref.extractall(temp_archive_dir)
                                log.debug(f"Extracted {path.name} to {temp_archive_dir}")

                                process_folder(
                                    Path(temp_archive_dir),
                                    output_subdir / path.stem, # Output for extracted content
                                    lang,
                                    force_ocr,
                                    skip_text,
                                    convert_office,
                                    optimize,
                                    progress_callback=progress_callback, # Pass callback recursively
                                )
                            except zipfile.BadZipFile:
                                log.error(f"Cannot process {path.name}, not a valid zip file or format not supported.")
                            except Exception as e:
                                log.error(f"Failed to extract or process archive {path.name}: {e}")

                except FileNotFoundError as e:
                    log.error(f"FileNotFoundError while processing {path.name}: {e}", exc_info=True)
                except Exception as e:
                    log.error(f"An unexpected error occurred while processing {path.name}: {e}", exc_info=True)

                finally:
                    if temp_pdf_path and temp_pdf_path.exists():
                        temp_pdf_path.unlink()
        except Exception as e:
            log.error(f"An unhandled error occurred in process_folder: {e}", exc_info=True)
            raise

    log.info("Conversion and OCR process completed.")
