"""
Module for merging multiple PDFs into a single file with hierarchical bookmarks using pypdf.

This module uses pypdf to:
1. Recursively scan a directory for PDF files.
2. Append all found PDFs into a single master PDF.
3. Build and set a hierarchical table of contents (bookmarks) that mirrors the
   original folder structure.
"""

import logging
from pathlib import Path
from typing import List, Optional

from pypdf import PdfWriter, PdfReader
from rich.progress import Progress

log = logging.getLogger(__name__)


def _build_toc_and_merge(
    writer: PdfWriter,
    folder_path: Path,
    toc_depth: int,
    current_depth: int,
    parent_bookmark: Optional[str] = None,
) -> None:
    """
    Recursively builds a TOC (bookmarks) for pypdf and merges PDFs into the writer.

    Args:
        writer: The PdfWriter object to merge into and add bookmarks to.
        folder_path: The current folder to process.
        toc_depth: Maximum depth for the TOC.
        current_depth: The current recursion depth.
        parent_bookmark: The parent bookmark for the current level.
    """
    if current_depth > toc_depth:
        return

    # Sort entries to ensure consistent order
    entries = sorted(list(folder_path.iterdir()), key=lambda p: p.name)

    for entry in entries:
        if entry.is_dir():
            # For a folder, add a bookmark for the folder itself
            if current_depth <= toc_depth:
                # Get the current page number before merging content of the folder
                # This will be the page where the folder's content starts
                folder_page_num = len(writer.pages)
                folder_bookmark = writer.add_outline_item(
                    entry.name, folder_page_num, parent=parent_bookmark
                )
                _build_toc_and_merge(
                    writer, entry, toc_depth, current_depth + 1, folder_bookmark
                )
            else:
                # If current_depth > toc_depth, still merge content but don't add bookmark
                _build_toc_and_merge(
                    writer, entry, toc_depth, current_depth + 1, parent_bookmark
                )

        elif entry.is_file() and entry.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(entry)
                # Add bookmark for the PDF file
                if current_depth <= toc_depth:
                    file_page_num = len(writer.pages) # 0-indexed
                    writer.add_outline_item(
                        entry.stem, file_page_num, parent=parent_bookmark
                    )
                writer.append(reader)
                log.debug(f"Appended {entry.name} to the final PDF.")
            except Exception as e:
                log.warning(
                    f"Could not process PDF {entry.name}. It may be corrupt or incompatible. Error: {e}"
                )


def merge_pdfs(
    input_dir: Path,
    output_file: Path,
    toc_depth: int = 3,
) -> None:
    """
    Merges all PDFs in a directory into a single file with a hierarchical TOC using pypdf.

    Args:
        input_dir: The directory containing the processed PDFs.
        output_file: The path for the final merged PDF.
        toc_depth: The maximum depth for the table of contents.
    """
    pdf_files = list(input_dir.rglob("*.pdf"))
    if not pdf_files:
        log.warning("No PDF files found to merge.")
        return

    log.info(f"Merging {len(pdf_files)} PDF files into {output_file.name}...")

    with PdfWriter() as writer:
        with Progress() as progress:
            task = progress.add_task("[magenta]Merging PDFs...", total=1)

            _build_toc_and_merge(
                writer, folder_path=input_dir, toc_depth=toc_depth, current_depth=1
            )

            progress.update(task, advance=1)

        if len(writer.pages) > 0:
            log.info(f"Saving final PDF to {output_file}...")
            writer.write(output_file)
            log.info("Merge complete.")
        else:
            log.warning("No pages were added. Output file not created.")
