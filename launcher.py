from __future__ import annotations

import threading
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import AppConfig, apply_overrides, default_config
from generador_horarios.pipeline import run_pipeline


class GeneratorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Generador Basket Aranjuez")
        self.geometry("650x430")
        self.minsize(600, 390)

        defaults = default_config()
        self.excel_path = tk.StringVar(value=str(defaults.excel_path))
        self.results_doc_path = tk.StringVar()
        self.mode = tk.StringVar(value="horarios")
        self.status = tk.StringVar(value="Selecciona un Excel y pulsa Generar.")
        self.generate_button: ttk.Button | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Generador Basket Aranjuez", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 22)
        )
        ttk.Label(frame, text="Archivo Excel").grid(row=1, column=0, sticky="w", pady=7)
        ttk.Entry(frame, textvariable=self.excel_path).grid(row=1, column=1, sticky="ew", pady=7, padx=10)
        ttk.Button(frame, text="Buscar...", command=self._choose_excel).grid(row=1, column=2, pady=7)

        ttk.Label(frame, text="Modo").grid(row=2, column=0, sticky="w", pady=7)
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=7)
        ttk.Radiobutton(mode_frame, text="Horarios", variable=self.mode, value="horarios", command=self._toggle_results).pack(
            side="left", padx=(0, 18)
        )
        ttk.Radiobutton(mode_frame, text="Resultados", variable=self.mode, value="resultados", command=self._toggle_results).pack(
            side="left"
        )

        self.results_label = ttk.Label(frame, text="Documento de resultados")
        self.results_label.grid(row=3, column=0, sticky="w", pady=7)
        self.results_entry = ttk.Entry(frame, textvariable=self.results_doc_path)
        self.results_entry.grid(row=3, column=1, sticky="ew", pady=7, padx=10)
        self.results_button = ttk.Button(frame, text="Buscar...", command=self._choose_results)
        self.results_button.grid(row=3, column=2, pady=7)

        ttk.Separator(frame).grid(row=4, column=0, columnspan=3, sticky="ew", pady=22)
        ttk.Label(frame, textvariable=self.status, wraplength=580).grid(row=5, column=0, columnspan=3, sticky="w")
        self.generate_button = ttk.Button(frame, text="Generar imágenes", command=self._start_generation)
        self.generate_button.grid(row=6, column=0, columnspan=3, pady=24, ipadx=18, ipady=7)
        self._toggle_results()

    def _toggle_results(self) -> None:
        state = "normal" if self.mode.get() == "resultados" else "disabled"
        self.results_entry.configure(state=state)
        self.results_button.configure(state=state)
        self.results_label.configure(state=state)

    def _choose_excel(self) -> None:
        selected = filedialog.askopenfilename(
            title="Selecciona el Excel de partidos",
            filetypes=[("Excel", "*.xlsx *.xlsm"), ("Todos los archivos", "*.*")],
        )
        if selected:
            self.excel_path.set(selected)

    def _choose_results(self) -> None:
        selected = filedialog.askopenfilename(
            title="Selecciona el documento de resultados",
            filetypes=[("Word", "*.docx"), ("Todos los archivos", "*.*")],
        )
        if selected:
            self.results_doc_path.set(selected)

    def _start_generation(self) -> None:
        if not self.excel_path.get().strip():
            messagebox.showerror("Falta el Excel", "Selecciona el Excel de partidos.")
            return
        if self.mode.get() == "resultados" and not self.results_doc_path.get().strip():
            messagebox.showerror("Falta el documento", "Selecciona el documento .docx de resultados.")
            return
        assert self.generate_button is not None
        self.generate_button.configure(state="disabled")
        self.status.set("Generando imágenes, espera un momento...")
        threading.Thread(target=self._run_generation, daemon=True).start()

    def _run_generation(self) -> None:
        try:
            defaults = default_config()
            config: AppConfig = apply_overrides(
                defaults,
                mode=self.mode.get(),
                excel_path=Path(self.excel_path.get()).expanduser().resolve(),
                results_doc_path=(
                    Path(self.results_doc_path.get()).expanduser().resolve()
                    if self.mode.get() == "resultados"
                    else None
                ),
            )
            result = run_pipeline(config)
            message = (
                f"Listo. {len(result.images)} imágenes creadas.\n"
                f"Carpeta: {result.output_dir}\n"
                f"Partidos procesados: {result.rendered_count} | Omitidos: {result.skipped_count}"
            )
            self.after(0, lambda: self._finish(message, success=True))
        except Exception as exc:  # The GUI should show a useful error instead of closing.
            self.after(0, lambda: self._finish(f"No se pudo completar la generación:\n{exc}", success=False))

    def _finish(self, message: str, *, success: bool) -> None:
        self.status.set(message)
        assert self.generate_button is not None
        self.generate_button.configure(state="normal")
        if success:
            messagebox.showinfo("Generación completada", message)
        else:
            messagebox.showerror("Error", message)


if __name__ == "__main__":
    GeneratorApp().mainloop()
