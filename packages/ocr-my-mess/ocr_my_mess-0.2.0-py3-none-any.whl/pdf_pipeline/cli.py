"""
Command-Line Interface for the ocr-my-mess project.

This module provides a CLI powered by Typer with two main commands:
- `convert`: To process a directory of documents, converting and running OCR.
- `merge`: To combine all resulting PDFs into a single file with bookmarks.
"""
import logging
import shutil
import sys
from pathlib import Path
from importlib import metadata
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

# Add project root to sys.path for absolute imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pdf_pipeline import convert as convert_module, merge as merge_module, utils  # noqa: E402

def version_callback(value: bool):
    if value:
        try:
            version = metadata.version("ocr-my-mess")
        except metadata.PackageNotFoundError:
            version = "unknown"
        print(f"ocr-my-mess version: {version}")
        raise typer.Exit()

app = typer.Typer(
    name="ocr-my-mess",
    help="A tool to convert, OCR, and merge documents into a single searchable PDF.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show the application's version and exit.",
    )
):
    """
    OCR My Mess: A tool to convert, OCR, and merge documents.
    """
    pass


@app.command()
def run(
    input_dir: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="The source directory containing all documents.",
        ),
    ],
    output_file: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            resolve_path=True,
            help="The final merged PDF file.",
        ),
    ],
    lang: Annotated[
        str, typer.Option("--lang", "-l", help="OCR language(s), e.g., 'eng+fra'.")
    ] = "fra",
    force_ocr: Annotated[
        bool,
        typer.Option("--force-ocr", help="Force OCR even if text is already present."),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity level (-v for INFO, -vv for DEBUG, -vvv for detailed DEBUG).",
        ),
    ] = 0,
    optimize: Annotated[
        int,
        typer.Option(
            "--optimize",
            "-O",
            min=0,
            max=3,
            help="PDF optimization level (0=none, 1=safe, 2=all, 3=unsafe)." ,
        ),
    ] = 0,
):
    """Run the full pipeline: convert, OCR, and merge all documents."""
    log_levels = ["WARNING", "INFO", "DEBUG", "DEBUG"]
    log_level = log_levels[min(verbose, len(log_levels) - 1)]
    deep_log = verbose >= 3
    utils.setup_logging(log_level, deep_log)

    log = logging.getLogger(__name__)
    if verbose > 0:
        log.info("OCR-my-mess starting with the following OCR options:")
        log.info(f"  Language: {lang}")
        log.info(f"  Force OCR: {force_ocr}")
        log.info(f"  Optimize: {optimize}")

    force_ocr_param = force_ocr
    skip_text_param = not force_ocr

    console.print("[bold purple]Starting full pipeline...[/bold purple]")

    cache_dir = Path(".ocr-my-mess-cache")
    if cache_dir.exists():
        reuse_cache = typer.confirm(
            f"Found existing cache directory '{cache_dir}'. Do you want to reuse it to resume processing?",
            default=True
        )
        if not reuse_cache:
            console.print(f"Clearing existing cache at {cache_dir}...")
            shutil.rmtree(cache_dir)

    cache_dir.mkdir(exist_ok=True)
    console.print(f"Intermediate files will be stored in: {cache_dir}")

    # --- Page Count ---
    console.print("[bold blue]Scanning files to estimate page count...[/bold blue]")
    file_generators = [
        input_dir.rglob(f"*{ext}") for ext in utils.SUPPORTED_IMAGE_EXTENSIONS
    ]
    # In the full pipeline, office conversion is always attempted
    file_generators.extend(
        [input_dir.rglob(f"*{ext}") for ext in utils.SUPPORTED_OFFICE_EXTENSIONS]
    )
    file_generators.extend(
        [input_dir.rglob(f"*{ext}") for ext in utils.SUPPORTED_ARCHIVE_EXTENSIONS]
    )
    file_generators.append(input_dir.rglob(f"*{utils.SUPPORTED_PDF_EXTENSION}"))
    all_files = {path for gen in file_generators for path in gen if path.is_file()}
    
    total_pages = utils.count_pages(all_files)
    console.print(f"[bold green]Estimated total pages to be processed: {total_pages}[/bold green]")
    # --- End Page Count ---

    # 1. Convert and OCR
    convert_module.process_folder(
        input_dir=input_dir,
        output_dir=cache_dir,
        lang=lang,
        force_ocr=force_ocr_param,
        skip_text=skip_text_param,
        convert_office=True,
        optimize=optimize,
    )

    # 2. Merge
    merge_module.merge_pdfs(
        input_dir=cache_dir,
        output_file=output_file,
    )

    console.print(f"[bold green]Pipeline complete! Final PDF is at: {output_file}[/bold green]")


@app.command()
def convert(
    input_dir: Annotated[
        Path,
        typer.Option(
            "--input-dir",
            "-i",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="The directory containing documents to process.",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True,
            help="The directory to save the processed PDFs.",
        ),
    ],
    lang: Annotated[
        str, typer.Option("--lang", "-l", help="OCR language(s), e.g., 'eng+fra'.")
    ] = "fra",
    force_ocr: Annotated[
        bool,
        typer.Option("--force-ocr", help="Force OCR even if text is already present."),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity level (-v for INFO, -vv for DEBUG, -vvv for detailed DEBUG).",
        ),
    ] = 0,
    convert_office: Annotated[
        bool,
        typer.Option(
            "--convert-office",
            "--no-convert-office",
            is_flag=True,
            show_default=False,
            help="Enable/disable office document conversion.",
        ),
    ] = True,
    optimize: Annotated[
        int,
        typer.Option(
            "--optimize",
            "-O",
            min=0,
            max=3,
            help="PDF optimization level (0=none, 1=safe, 2=all, 3=unsafe).",
        ),
    ] = 0,
):
    """Convert and OCR all documents in a directory."""
    log_levels = ["WARNING", "INFO", "DEBUG", "DEBUG"]
    log_level = log_levels[min(verbose, len(log_levels) - 1)]
    deep_log = verbose >= 3
    utils.setup_logging(log_level, deep_log)

    log = logging.getLogger(__name__)
    if verbose > 0:
        log.info("OCR-my-mess starting with the following OCR options:")
        log.info(f"  Language: {lang}")
        log.info(f"  Force OCR: {force_ocr}")
        log.info(f"  Optimize: {optimize}")
        log.debug(f"convert_office: {convert_office}")

    force_ocr_param = force_ocr
    skip_text_param = not force_ocr

    console.print("[bold green]Starting conversion process...[/bold green]")
    console.print(f"  [cyan]Input directory[/cyan]: {input_dir}")
    console.print(f"  [cyan]Output directory[/cyan]: {output_dir}")
    console.print(f"  [cyan]OCR Language(s)[/cyan]: {lang}")

    convert_module.process_folder(
        input_dir=input_dir,
        output_dir=output_dir,
        lang=lang,
        force_ocr=force_ocr_param,
        skip_text=skip_text_param,
        convert_office=convert_office,
        optimize=optimize,
    )
    console.print("[bold green]Conversion complete![/bold green]")


@app.command()
def merge(
    input_dir: Annotated[
        Path,
        typer.Option(
            "--input-dir",
            "-i",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="The directory containing the PDFs to merge.",
        ),
    ],
    output_file: Annotated[
        Path,
        typer.Option(
            "--output-file",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            resolve_path=True,
            help="The final merged PDF file.",
        ),
    ],
    toc_depth: Annotated[
        int, typer.Option("--toc-depth", help="Maximum depth for the table of contents.")
    ] = 3,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity level (-v for INFO, -vv for DEBUG, -vvv for detailed DEBUG).",
        ),
    ] = 0,
):
    """Merge all PDFs in a directory into a single file with a table of contents."""
    log_levels = ["WARNING", "INFO", "DEBUG", "DEBUG"]
    log_level = log_levels[min(verbose, len(log_levels) - 1)]
    deep_log = verbose >= 3
    utils.setup_logging(log_level, deep_log)

    console.print("[bold blue]Starting merge process...[/bold blue]")
    console.print(f"  [cyan]Input directory[/cyan]: {input_dir}")
    console.print(f"  [cyan]Output file[/cyan]: {output_file}")

    merge_module.merge_pdfs(input_dir=input_dir, output_file=output_file, toc_depth=toc_depth)
    console.print("[bold blue]Merge complete![/bold blue]")


def main():
    app()


if __name__ == "__main__":
    main()