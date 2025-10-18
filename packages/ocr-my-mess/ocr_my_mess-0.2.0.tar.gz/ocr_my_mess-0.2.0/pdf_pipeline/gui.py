"""
Graphical User Interface for the ocr-my-mess project.

This module provides a simple GUI built with Tkinter. It allows users to:
- Select input and output directories.
- Specify OCR languages.
- Trigger the conversion and merging processes.
- View live logs and progress updates.

The core processing logic is run in a separate thread to keep the GUI responsive.
"""
import logging
import queue
import shutil
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
from typing import Optional
from importlib import metadata

import ttkbootstrap as ttk
from ttkbootstrap.constants import (BOTH, DANGER, FLAT, LEFT, SECONDARY, SUCCESS, X)

# Add project root to sys.path for absolute imports when bundled by PyInstaller
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pdf_pipeline import convert as convert_module, merge as merge_module, utils  # noqa: E402


class QueueHandler(logging.Handler):
    """A logging handler that sends records to a queue."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class App(ttk.Window):
    """The main application window for the ocr-my-mess GUI."""

    def __init__(self):
        super().__init__(themename="litera")
        try:
            version = metadata.version("ocr-my-mess")
        except metadata.PackageNotFoundError:
            version = "unknown"
        self.title(f"OCR My Mess v{version}")
        self.geometry("800x750")

        self.thread = None
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.start_time = 0
        self.final_pdf_path: Optional[Path] = None

        self.source_dir = tk.StringVar()
        self.dest_file = tk.StringVar()

        utils.setup_logging("INFO")
        self.logger = logging.getLogger()
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        self.logger.addHandler(QueueHandler(self.log_queue))

        self.create_widgets()
        self.after(100, self.process_queues)

    def create_widgets(self):
        """Create and layout all the widgets in the main window."""
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=BOTH, expand=True)

        # --- Files Frame ---
        files_frame = ttk.LabelFrame(main_frame, text="Fichiers", padding="10")
        files_frame.pack(fill=X, pady=5)

        # Source Directory
        source_frame = ttk.Frame(files_frame)
        source_frame.pack(fill=X, expand=True, pady=(0, 5))
        ttk.Label(source_frame, text="Dossier Source:").pack(side=LEFT)
        ttk.Entry(source_frame, textvariable=self.source_dir).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(source_frame, text="Parcourir...", command=self.browse_source_directory).pack(side=LEFT)

        # Destination File
        dest_frame = ttk.Frame(files_frame)
        dest_frame.pack(fill=X, expand=True)
        ttk.Label(dest_frame, text="PDF Destination:").pack(side=LEFT)
        ttk.Entry(dest_frame, textvariable=self.dest_file).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(dest_frame, text="Parcourir...", command=self.browse_destination_file).pack(side=LEFT)

        # --- Options Frame ---
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.pack(fill=X, pady=10)

        self.lang = tk.StringVar(value="fra")
        self.force_pdf = tk.BooleanVar()
        self.optimize_level = tk.IntVar(value=0)

        lang_frame = ttk.Frame(options_frame)
        lang_frame.pack(fill=X, expand=True, pady=5)
        ttk.Label(lang_frame, text="Langue(s) OCR:").pack(side=LEFT, padx=(0, 5))
        ttk.Entry(lang_frame, textvariable=self.lang).pack(side=LEFT, fill=X, expand=True, padx=5)

        ttk.Label(lang_frame, text="Niveau d'optimisation:").pack(side=LEFT, padx=(10, 5))
        ttk.Combobox(
            lang_frame,
            textvariable=self.optimize_level,
            values=[0, 1, 2, 3],
            width=5,
            state="readonly",
        ).pack(side=LEFT, padx=5)

        check_frame = ttk.Frame(options_frame)
        check_frame.pack(fill=X, expand=True, pady=5)
        ttk.Checkbutton(
            check_frame, text="Forcer l\'OCR sur tous les PDFs", variable=self.force_pdf, bootstyle="round-toggle"
        ).pack(side=LEFT, padx=10)

        # --- Action Frame ---
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        action_frame.pack(fill=X, pady=10)

        self.run_button = ttk.Button(
            action_frame, text="Lancer le Pipeline Complet", command=self.start_full_pipeline, bootstyle=SUCCESS
        )
        self.run_button.pack(side=LEFT, fill=X, expand=True, ipady=10, padx=(0, 5))

        self.open_pdf_button = ttk.Button(
            action_frame, text="Ouvrir le PDF", command=self.open_final_pdf, bootstyle=SECONDARY, state="disabled"
        )
        self.open_pdf_button.pack(side=LEFT, ipady=10, padx=(5, 0))

        # --- Progress Frame ---
        progress_frame = ttk.LabelFrame(main_frame, text="Progression", padding="10")
        progress_frame.pack(fill=X, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode='determinate'
        )
        self.progress_bar.pack(fill=X, expand=True, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="En attente...")
        self.progress_label.pack(fill=X, expand=True)

        # --- Log Frame ---
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        log_frame.pack(fill=BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, state="disabled", height=10, relief=FLAT)
        self.log_text.pack(fill=BOTH, expand=True)
        self.log_text.tag_config("INFO", foreground="#00006b")
        self.log_text.tag_config("WARNING", foreground="#b8860b")
        self.log_text.tag_config("ERROR", foreground="#ff0000")
        self.log_text.tag_config("DEBUG", foreground="#808080")

    def browse_source_directory(self):
        path = filedialog.askdirectory(title="Sélectionnez le dossier source")
        if path:
            self.source_dir.set(path)

    def browse_destination_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            title="Enregistrer le PDF final",
        )
        if path:
            self.dest_file.set(path)

    def process_queues(self):
        self.process_log_queue()
        self.process_progress_queue()
        self.after(100, self.process_queues)

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                msg = record.getMessage()
                self.log_text.configure(state="normal")
                self.log_text.insert(tk.END, msg + "\n", record.levelname)
                self.log_text.configure(state="disabled")
                self.log_text.yview(tk.END)
        except queue.Empty:
            pass

    def process_progress_queue(self):
        try:
            while True:
                current, total = self.progress_queue.get_nowait()
                if total > 0:
                    percentage = (current / total) * 100
                    self.progress_var.set(percentage)

                    elapsed_time = time.time() - self.start_time
                    if current > 0:
                        time_per_item = elapsed_time / current
                        remaining_items = total - current
                        eta = remaining_items * time_per_item
                        
                        eta_seconds = int(eta)
                        hours, remainder = divmod(eta_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        if hours > 0:
                            eta_str = f"{hours}h {minutes}m {seconds}s"
                        elif minutes > 0:
                            eta_str = f"{minutes}m {seconds}s"
                        else:
                            eta_str = f"{seconds}s"
                        label_text = f"Fichier {current}/{total} | Temps restant estimé: {eta_str}"
                    else:
                        label_text = f"Fichier {current}/{total}"
                    self.progress_label.config(text=label_text)
        except queue.Empty:
            pass

    def start_full_pipeline(self):
        input_dir = self.source_dir.get()
        output_file = self.dest_file.get()

        if not input_dir or not output_file:
            messagebox.showwarning("Champs manquants", "Veuillez sélectionner un dossier source et un fichier de destination.")
            return

        cache_dir = Path(".ocr-my-mess-cache")
        if cache_dir.exists():
            reuse_cache = messagebox.askyesno(
                "Cache existant trouvé",
                f"Le dossier cache '{cache_dir}' existe déjà.\nVoulez-vous le réutiliser pour continuer le traitement ?"
            )
            if not reuse_cache:
                self.logger.info(f"Suppression du cache existant: {cache_dir}")
                try:
                    shutil.rmtree(cache_dir)
                except OSError as e:
                    self.logger.error(f"Erreur lors de la suppression du cache: {e}")
                    messagebox.showerror("Erreur de cache", f"Impossible de supprimer le dossier cache: {e}")
                    return

        self.final_pdf_path = Path(output_file)
        self.start_task(
            self._full_pipeline_worker,
            Path(input_dir),
            self.final_pdf_path,
        )

    def open_final_pdf(self):
        if self.final_pdf_path and self.final_pdf_path.exists():
            webbrowser.open(self.final_pdf_path.as_uri())
        else:
            messagebox.showwarning("Fichier non trouvé", "Le fichier PDF final n'a pas été trouvé ou n'a pas encore été créé.")

    def _progress_callback(self, current, total):
        self.progress_queue.put((current, total))

    def stop_task(self):
        if self.thread and self.thread.is_alive():
            self.logger.info("Arrêt du traitement demandé par l'utilisateur...")
            self.stop_event.set()

    def start_task(self, target, *args):
        if self.thread and self.thread.is_alive():
            messagebox.showwarning("Occupé", "Une tâche est déjà en cours.")
            return

        self.stop_event.clear()
        self.open_pdf_button.config(state="disabled", bootstyle=SECONDARY)
        self.run_button.config(text="Arrêter le traitement", command=self.stop_task, bootstyle=DANGER)
        self.progress_var.set(0)
        self.progress_label.config(text="Démarrage...")
        self.start_time = time.time()

        self.thread = threading.Thread(target=target, args=args, daemon=True)
        self.thread.start()
        self.after(100, self.check_thread)

    def _full_pipeline_worker(self, input_dir, output_file):
        try:
            cache_dir = Path(".ocr-my-mess-cache")
            cache_dir.mkdir(exist_ok=True)
            self.logger.info(f"Utilisation du dossier cache: {cache_dir}")

            force_ocr = self.force_pdf.get()
            skip_text = not force_ocr

            convert_module.process_folder(
                input_dir=input_dir,
                output_dir=cache_dir,
                lang=self.lang.get(),
                force_ocr=force_ocr,
                skip_text=skip_text,
                optimize=self.optimize_level.get(),
                progress_callback=self._progress_callback,
                stop_event=self.stop_event,
            )

            if self.stop_event.is_set():
                self.logger.warning("Le traitement a été arrêté.")
                return

            self.logger.info("Fusion des PDFs...")
            merge_module.merge_pdfs(input_dir=cache_dir, output_file=output_file)

            self.logger.info(f"Pipeline terminé ! Fichier final: {output_file}")
        except Exception as e:
            self.logger.error(f"Erreur durant le pipeline: {e}", exc_info=True)

    def check_thread(self):
        if self.thread and self.thread.is_alive():
            self.after(100, self.check_thread)
        else:
            self.run_button.config(text="Lancer le Pipeline Complet", command=self.start_full_pipeline, bootstyle=SUCCESS)
            if self.thread:
                if self.stop_event.is_set():
                    self.progress_label.config(text="Tâche annulée.")
                else:
                    self.progress_var.set(100)
                    self.progress_label.config(text="Tâche terminée !")
                    self.open_pdf_button.config(state="normal", bootstyle=SUCCESS)
                    messagebox.showinfo("Terminé", "La tâche est terminée !")
            self.thread = None

def main():
    """The main entry point for the GUI application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()