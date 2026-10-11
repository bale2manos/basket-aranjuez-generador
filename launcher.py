from __future__ import annotations

import os
import argparse
import json
from pathlib import Path
from queue import Empty, Queue
import sys
from threading import Thread
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import AppConfig, apply_overrides, default_config
from generador_horarios.design import DESIGN_VERSION, SEASON
from generador_horarios.pipeline import run_pipeline
from generador_horarios.resources import validate_render_assets


class GeneratorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Basket Aranjuez - Generador {DESIGN_VERSION} - {SEASON}")
        self.geometry("760x490")
        self.minsize(660, 470)
        defaults = default_config()
        self.excel_path = tk.StringVar(value=str(defaults.excel_path))
        self.background_path = tk.StringVar(value=str(defaults.background_image_path))
        self.results_doc_path = tk.StringVar(value=str(defaults.results_doc_path or ""))
        self.mode = tk.StringVar(value=defaults.mode)
        self.output_root_dir = defaults.output_root_dir
        self.status = tk.StringVar(value="Selecciona el Excel y pulsa Generar imagenes.")
        self.messages: Queue = Queue()
        self.running = False
        self.last_output: Path | None = None
        self.input_controls: list[ttk.Widget] = []
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=f"Basket Aranjuez {SEASON}", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 20),
        )
        self._path_row(frame, 1, "Excel de partidos", self.excel_path, [("Excel", "*.xlsx *.xlsm")])
        self._path_row(frame, 2, "Foto de fondo", self.background_path, [("Imagen", "*.jpg *.jpeg *.png")])
        ttk.Label(frame, text="Modo").grid(row=3, column=0, sticky="w", pady=8)
        modes = ttk.Frame(frame)
        modes.grid(row=3, column=1, sticky="w", padx=10)
        for value, label in (("horarios", "Horarios"), ("resultados", "Resultados")):
            button = ttk.Radiobutton(modes, text=label, variable=self.mode, value=value, command=self._toggle_results)
            button.pack(side="left", padx=(0, 18))
            self.input_controls.append(button)
        self.results_entry, self.results_button = self._path_row(
            frame, 4, "Resultados (.docx)", self.results_doc_path, [("Word", "*.docx")],
        )
        ttk.Separator(frame).grid(row=5, column=0, columnspan=3, sticky="ew", pady=18)
        ttk.Label(frame, textvariable=self.status, wraplength=690).grid(row=6, column=0, columnspan=3, sticky="w")
        actions = ttk.Frame(frame)
        actions.grid(row=7, column=0, columnspan=3, pady=24)
        self.generate_button = ttk.Button(actions, text="Generar imagenes", command=self._start_generation)
        self.generate_button.pack(side="left", padx=8, ipadx=14, ipady=6)
        self.open_button = ttk.Button(actions, text="Abrir carpeta generada", command=self._open_output, state="disabled")
        self.open_button.pack(side="left", padx=8, ipadx=8, ipady=6)
        self._toggle_results()

    def _path_row(self, frame, row, label, variable, filetypes):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=8)
        entry = ttk.Entry(frame, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
        button = ttk.Button(frame, text="Buscar...", command=lambda: self._choose_path(variable, label, filetypes))
        button.grid(row=row, column=2, pady=8)
        self.input_controls.extend((entry, button))
        return entry, button

    def _choose_path(self, variable, title, filetypes) -> None:
        selected = filedialog.askopenfilename(title=title, filetypes=[*filetypes, ("Todos", "*.*")])
        if selected:
            variable.set(selected)

    def _toggle_results(self) -> None:
        state = "normal" if self.mode.get() == "resultados" and not self.running else "disabled"
        self.results_entry.configure(state=state)
        self.results_button.configure(state=state)

    def _start_generation(self) -> None:
        if self.running:
            return
        try:
            if not self.excel_path.get().strip():
                raise ValueError("Selecciona el Excel de partidos.")
            if self.mode.get() == "resultados" and not self.results_doc_path.get().strip():
                raise ValueError("Selecciona el documento .docx de resultados.")
            if not self.background_path.get().strip():
                raise ValueError("Selecciona la foto de fondo.")
            # Read all Tk variables on the UI thread before launching the worker.
            config = apply_overrides(
                default_config(), mode=self.mode.get(),
                excel_path=Path(self.excel_path.get()).expanduser().resolve(),
                background_image_path=Path(self.background_path.get()).expanduser().resolve(),
                output_root_dir=self.output_root_dir,
                results_doc_path=Path(self.results_doc_path.get()).expanduser().resolve() if self.mode.get() == "resultados" else None,
            )
            validate_render_assets(config)
        except (ValueError, OSError) as exc:
            self.status.set(str(exc))
            messagebox.showerror("Revisa los archivos", str(exc))
            return
        self.running = True
        self.generate_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        for widget in self.input_controls:
            widget.configure(state="disabled")
        self.status.set("Generando imagenes, espera un momento...")
        Thread(target=self._run_generation, args=(config,), daemon=True).start()
        self.after(100, self._poll_messages)

    def _run_generation(self, config: AppConfig) -> None:
        try:
            result = run_pipeline(config)
            message = (
                f"{len(result.images)} imagenes creadas. Partidos: {result.rendered_count}; omitidos: {result.skipped_count}.\n"
                f"Carpeta: {result.output_dir}"
            )
            self.messages.put((True, message, result.output_dir))
        except Exception as exc:
            self.messages.put((False, f"No se pudo completar la generacion:\n{exc}", None))

    def _poll_messages(self) -> None:
        try:
            success, message, output_dir = self.messages.get_nowait()
        except Empty:
            self.after(100, self._poll_messages)
            return
        self.running = False
        self.status.set(message)
        self.generate_button.configure(state="normal")
        for widget in self.input_controls:
            widget.configure(state="normal")
        self._toggle_results()
        if success:
            self.last_output = output_dir
            self.open_button.configure(state="normal")
            messagebox.showinfo("Generacion completada", message)
        else:
            messagebox.showerror("Error de generacion", message)

    def _open_output(self) -> None:
        if self.last_output is not None:
            os.startfile(self.last_output)

    def _close(self) -> None:
        if self.running:
            messagebox.showinfo("Generando imagenes", "Espera a que termine la generacion para cerrar.")
        else:
            self.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplicacion Basket Aranjuez 2.0")
    parser.add_argument("--mode", choices=("horarios", "resultados"))
    parser.add_argument("--excel-path", type=Path)
    parser.add_argument("--results-doc-path", type=Path)
    parser.add_argument("--output-root-dir", type=Path)
    parser.add_argument("--verify-package", action="store_true", help="Comprueba la generacion desde la interfaz y escribe _package_check.json.")
    args = parser.parse_args()
    app = GeneratorApp()
    if args.mode:
        app.mode.set(args.mode)
        app._toggle_results()
    if args.excel_path:
        app.excel_path.set(str(args.excel_path.resolve()))
    if args.results_doc_path:
        app.results_doc_path.set(str(args.results_doc_path.resolve()))
    if args.output_root_dir:
        app.output_root_dir = args.output_root_dir.resolve()
    if not args.verify_package:
        app.mainloop()
        return 0

    # Exercise the real button, Tk event loop and worker in the frozen package.
    app.withdraw()
    outcome: dict[str, object] = {}
    started = time.monotonic()
    messagebox.showinfo = lambda title, message: outcome.update(success=True, message=message)
    messagebox.showerror = lambda title, message: outcome.update(success=False, message=message)

    def finish_check() -> None:
        if not outcome and time.monotonic() - started < 60:
            app.after(100, finish_check)
            return
        if not outcome:
            outcome.update(success=False, message="Tiempo de comprobacion agotado")
        outcome.update(mode=app.mode.get(), output_dir=str(app.last_output or ""), design_version=DESIGN_VERSION)
        app.output_root_dir.mkdir(parents=True, exist_ok=True)
        (app.output_root_dir / "_package_check.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
        app.destroy()

    app.after(20, app.generate_button.invoke)
    app.after(100, finish_check)
    app.mainloop()
    return 0 if outcome.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
