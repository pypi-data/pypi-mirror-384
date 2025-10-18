"""
Module of utility functions for the OCR My Mess project.

Contains helpers for:
- Setting up rich logging.
- Finding files recursively with specific extensions.
- Checking for the existence of external commands (like LibreOffice).
- Defining shared constants.
"""

import logging
import shutil
import threading
from pathlib import Path
from typing import Generator, List, Set

import pikepdf
from rich.logging import RichHandler

log = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]
SUPPORTED_OFFICE_EXTENSIONS = [".docx", ".odt", ".txt", ".rtf"]
SUPPORTED_ARCHIVE_EXTENSIONS = [".zip", ".tar", ".gz", ".rar"]
SUPPORTED_PDF_EXTENSION = ".pdf"

_log_context = threading.local()


class ContextFilter(logging.Filter):
    """A logging filter that injects contextual information into the log message."""

    def filter(self, record):
        prefix = ""
        if hasattr(_log_context, "filename"):
            prefix += f"[{_log_context.filename}] "
        elif hasattr(record, "input_file") and record.input_file:
            prefix += f"[{Path(record.input_file).name}] "
        
        if hasattr(record, "page_num") and record.page_num:
            prefix += f"Page {record.page_num}: "

        record.msg = f"{prefix}{record.msg}"
        return True


def set_log_context(filename: str):
    """Sets the filename in the logging context."""
    _log_context.filename = filename


def clear_log_context():
    """Clears the filename from the logging context."""
    if hasattr(_log_context, "filename"):
        del _log_context.filename


def setup_logging(level: str = "INFO", deep_log: bool = False) -> None:
    """Configure logging to use rich for beautiful, colorful output."""
    handler = RichHandler(rich_tracebacks=True, show_path=False)
    handler.addFilter(ContextFilter())

    # Configure root logger for our application
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )
    logging.getLogger("pdf_pipeline").setLevel(level)

    # Take control of the ocrmypdf and tesseract loggers
    for logger_name in ["ocrmypdf", "tesseract"]:
        logger = logging.getLogger(logger_name)
        logger.handlers = [] # Remove any existing handlers
        logger.addHandler(handler)
        logger.propagate = False # Don't forward to root logger
        logger.setLevel(level)

    if deep_log:
        logging.getLogger("pdf_pipeline").setLevel("DEBUG")
        logging.getLogger("ocrmypdf").setLevel("DEBUG")
        logging.getLogger("tesseract").setLevel("DEBUG")


def find_files(
    directory: Path, extensions: List[str]
) -> Generator[Path, None, None]:
    """
    Recursively find all files in a directory with the given extensions.

    Args:
        directory: The directory to search.
        extensions: A list of file extensions to look for (e.g., ['.txt', '.pdf']).

    Yields:
        Paths to the files found.
    """
    for extension in extensions:
        for path in directory.rglob(f"*{extension}"):
            if path.is_file():
                yield path


def check_command_exists(command: str) -> bool:
    """
    Check if a command-line tool is available on the system's PATH.

    Args:
        command: The name of the command to check (e.g., 'libreoffice').

    Returns:
        True if the command exists, False otherwise.
    """
    return shutil.which(command) is not None


def count_pages(files: Set[Path]) -> int:
    """
    Counts the total number of pages for a list of files (PDFs and images).
    """
    total_pages = 0
    ignored_types = set()

    log.info(f"Scanning {len(files)} files to estimate total page count...")

    for file in files:
        ext = file.suffix.lower()
        if ext == SUPPORTED_PDF_EXTENSION:
            try:
                with pikepdf.open(file) as pdf:
                    total_pages += len(pdf.pages)
            except Exception as e:
                log.warning(f"Could not open PDF {file.name} to count pages: {e}")
        elif ext in SUPPORTED_IMAGE_EXTENSIONS:
            total_pages += 1
        else:
            # This will catch office docs, archives, and anything else
            ignored_types.add(ext)

    if ignored_types:
        log.info(
            f"Note: Initial page count excludes archives, office documents, and other unsupported types ({', '.join(ignored_types)})."
        )

    return total_pages
