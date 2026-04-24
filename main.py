"""Modern QR studio with Tkinter UI plus environment diagnostics."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import argparse
import importlib.util
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, unquote_plus

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
except Exception:  # pragma: no cover - handled in runtime checks
    qrcode = None
    ERROR_CORRECT_L = ERROR_CORRECT_M = ERROR_CORRECT_Q = ERROR_CORRECT_H = None

try:
    from PIL import Image, ImageTk
except Exception:  # pragma: no cover - handled in runtime checks
    Image = None
    ImageTk = None

APP_DIR = Path(__file__).resolve().parent
HISTORY_FILE = APP_DIR / "history.json"
PREVIEW_SIZE = (240, 240)


@dataclass
class HistoryItem:
    timestamp: str
    mode: str
    payload: str
    output_file: str


class ModernQRStudio:
    def __init__(self, root: Any, tk: Any, ttk: Any, filedialog: Any, messagebox: Any, scrolled_text_cls: Any) -> None:
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.scrolled_text_cls = scrolled_text_cls
        self.root = root
        self.root.title("Modern QR Studio")
        self.root.geometry("920x640")
        self.root.minsize(840, 560)

        self.preview_image = None
        self.history: list[HistoryItem] = []

        self.payload_var = self.tk.StringVar(value="")
        self.filename_var = self.tk.StringVar(value="qrcode")
        self.fill_color_var = self.tk.StringVar(value="#111111")
        self.back_color_var = self.tk.StringVar(value="#ffffff")
        self.box_size_var = self.tk.StringVar(value="10")
        self.border_var = self.tk.StringVar(value="4")
        self.ec_var = self.tk.StringVar(value="M")
        self.batch_folder_var = self.tk.StringVar(value=str(APP_DIR / "exports"))

        self._build_ui()
        self._load_history()

    def _build_ui(self) -> None:
        self._build_styles()

        wrapper = self.ttk.Frame(self.root, padding=12)
        wrapper.pack(fill="both", expand=True)

        title = self.ttk.Label(
            wrapper,
            text="Modern QR Studio",
            font=("Segoe UI", 20, "bold"),
        )
        subtitle = self.ttk.Label(
            wrapper,
            text="QR generation, batch exports, and practical text tools in one desktop app.",
        )
        title.pack(anchor="w")
        subtitle.pack(anchor="w", pady=(0, 8))

        notebook = self.ttk.Notebook(wrapper)
        notebook.pack(fill="both", expand=True)

        self.generator_tab = self.ttk.Frame(notebook, padding=12)
        self.tools_tab = self.ttk.Frame(notebook, padding=12)
        self.history_tab = self.ttk.Frame(notebook, padding=12)

        notebook.add(self.generator_tab, text="QR Generator")
        notebook.add(self.tools_tab, text="Utilities")
        notebook.add(self.history_tab, text="History")

        self._build_generator_tab()
        self._build_tools_tab()
        self._build_history_tab()

    def _build_styles(self) -> None:
        style = self.ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

    def _build_generator_tab(self) -> None:
        left = self.ttk.Frame(self.generator_tab)
        right = self.ttk.Frame(self.generator_tab)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right.pack(side="right", fill="y")

        self.ttk.Label(left, text="Data / URL / Text", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.payload_text = self.scrolled_text_cls(left, height=10, wrap="word")
        self.payload_text.pack(fill="x", pady=(4, 10))

        form = self.ttk.LabelFrame(left, text="Customization", padding=10)
        form.pack(fill="x")

        self._field(form, "Default file name", self.filename_var, row=0)
        self._field(form, "Foreground color", self.fill_color_var, row=1)
        self._field(form, "Background color", self.back_color_var, row=2)
        self._field(form, "Box size", self.box_size_var, row=3)
        self._field(form, "Border", self.border_var, row=4)

        self.ttk.Label(form, text="Error correction").grid(row=5, column=0, sticky="w", pady=4)
        ec = self.ttk.Combobox(form, textvariable=self.ec_var, values=["L", "M", "Q", "H"], state="readonly", width=8)
        ec.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=4)

        action_row = self.ttk.Frame(left)
        action_row.pack(fill="x", pady=(10, 8))
        self.ttk.Button(action_row, text="Generate QR", command=self.generate_qr).pack(side="left")
        self.ttk.Button(action_row, text="Copy Payload", command=self.copy_payload).pack(side="left", padx=8)
        self.ttk.Button(action_row, text="Clear", command=self.clear_payload).pack(side="left")

        batch = self.ttk.LabelFrame(left, text="Batch Export (CSV)", padding=10)
        batch.pack(fill="x", pady=(8, 0))
        self.ttk.Label(batch, text="CSV format: first column is payload, optional second column is filename").pack(anchor="w")
        self.ttk.Entry(batch, textvariable=self.batch_folder_var).pack(fill="x", pady=6)
        batch_actions = self.ttk.Frame(batch)
        batch_actions.pack(fill="x")
        self.ttk.Button(batch_actions, text="Choose Export Folder", command=self.choose_export_folder).pack(side="left")
        self.ttk.Button(batch_actions, text="Run Batch Export", command=self.run_batch_export).pack(side="left", padx=8)

        preview_box = self.ttk.LabelFrame(right, text="Preview", padding=8)
        preview_box.pack(fill="both", expand=True)
        self.preview_label = self.ttk.Label(preview_box, text="No preview yet", width=34)
        self.preview_label.pack(fill="both", expand=True)

    def _field(self, parent: Any, label: str, variable: Any, row: int) -> None:
        self.ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        self.ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=4)
        parent.columnconfigure(1, weight=1)

    def _build_tools_tab(self) -> None:
        self.ttk.Label(self.tools_tab, text="Text Utilities", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.ttk.Label(self.tools_tab, text="Quickly transform text for common development and sharing tasks.").pack(anchor="w")

        self.tool_input = self.scrolled_text_cls(self.tools_tab, height=10, wrap="word")
        self.tool_input.pack(fill="x", pady=(8, 8))

        btns = self.ttk.Frame(self.tools_tab)
        btns.pack(fill="x")
        self.ttk.Button(btns, text="Base64 Encode", command=self.base64_encode).pack(side="left")
        self.ttk.Button(btns, text="Base64 Decode", command=self.base64_decode).pack(side="left", padx=6)
        self.ttk.Button(btns, text="URL Encode", command=self.url_encode).pack(side="left")
        self.ttk.Button(btns, text="URL Decode", command=self.url_decode).pack(side="left", padx=6)
        self.ttk.Button(btns, text="SHA256", command=self.sha256_hash).pack(side="left")

        self.tool_output = self.scrolled_text_cls(self.tools_tab, height=12, wrap="word")
        self.tool_output.pack(fill="both", expand=True, pady=(10, 0))

    def _build_history_tab(self) -> None:
        self.ttk.Label(self.history_tab, text="Recent Exports", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        columns = ("time", "mode", "output")
        self.history_tree = self.ttk.Treeview(self.history_tab, columns=columns, show="headings", height=18)
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("mode", text="Mode")
        self.history_tree.heading("output", text="Output")
        self.history_tree.column("time", width=170)
        self.history_tree.column("mode", width=100)
        self.history_tree.column("output", width=560)
        self.history_tree.pack(fill="both", expand=True, pady=(6, 6))

        actions = self.ttk.Frame(self.history_tab)
        actions.pack(fill="x")
        self.ttk.Button(actions, text="Refresh", command=self.refresh_history_view).pack(side="left")
        self.ttk.Button(actions, text="Clear History", command=self.clear_history).pack(side="left", padx=8)

    def _check_dependencies(self) -> bool:
        if qrcode is None or Image is None or ImageTk is None:
            self.messagebox.showerror(
                "Missing dependencies",
                "Please install dependencies first: pip install -r requirements.txt",
            )
            return False
        return True

    def _error_level(self):
        mapping = {
            "L": ERROR_CORRECT_L,
            "M": ERROR_CORRECT_M,
            "Q": ERROR_CORRECT_Q,
            "H": ERROR_CORRECT_H,
        }
        return mapping[self.ec_var.get()]

    def generate_qr(self) -> None:
        if not self._check_dependencies():
            return

        payload = self.payload_text.get("1.0", "end").strip()
        if not payload:
            self.messagebox.showwarning("Missing data", "Please provide text/data to encode.")
            return

        try:
            box_size = int(self.box_size_var.get())
            border = int(self.border_var.get())
        except ValueError:
            self.messagebox.showerror("Invalid number", "Box size and border must be integers.")
            return

        file_name = self.filename_var.get().strip() or "qrcode"
        save_path = self.filedialog.asksaveasfilename(
            title="Save QR code",
            defaultextension=".png",
            initialfile=f"{file_name}.png",
            filetypes=[("PNG", "*.png")],
        )
        if not save_path:
            return

        qr_obj = qrcode.QRCode(
            version=None,
            error_correction=self._error_level(),
            box_size=box_size,
            border=border,
        )
        qr_obj.add_data(payload)
        qr_obj.make(fit=True)

        image = qr_obj.make_image(fill_color=self.fill_color_var.get(), back_color=self.back_color_var.get()).convert("RGB")
        image.save(save_path)
        self._update_preview(save_path)

        self._record_history("single", payload, save_path)
        self.messagebox.showinfo("Saved", f"QR code saved to:\n{save_path}")

    def _update_preview(self, path: str) -> None:
        image = Image.open(path)
        image.thumbnail(PREVIEW_SIZE)
        self.preview_image = ImageTk.PhotoImage(image)
        self.preview_label.configure(image=self.preview_image, text="")

    def copy_payload(self) -> None:
        payload = self.payload_text.get("1.0", "end").strip()
        if not payload:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(payload)
        self.root.update()
        self.messagebox.showinfo("Copied", "Payload copied to clipboard.")

    def clear_payload(self) -> None:
        self.payload_text.delete("1.0", "end")

    def choose_export_folder(self) -> None:
        folder = self.filedialog.askdirectory(title="Choose export folder")
        if folder:
            self.batch_folder_var.set(folder)

    def run_batch_export(self) -> None:
        if not self._check_dependencies():
            return

        csv_file = self.filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV", "*.csv")])
        if not csv_file:
            return

        output_dir = Path(self.batch_folder_var.get()).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        with open(csv_file, newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            for index, row in enumerate(reader, start=1):
                if not row:
                    continue
                payload = row[0].strip()
                if not payload:
                    continue
                file_name = row[1].strip() if len(row) > 1 and row[1].strip() else f"qr_{index}"
                target = output_dir / f"{file_name}.png"
                qr_obj = qrcode.QRCode(
                    error_correction=self._error_level(),
                    box_size=max(1, int(self.box_size_var.get())),
                    border=max(1, int(self.border_var.get())),
                )
                qr_obj.add_data(payload)
                qr_obj.make(fit=True)
                image = qr_obj.make_image(fill_color=self.fill_color_var.get(), back_color=self.back_color_var.get()).convert("RGB")
                image.save(target)
                self._record_history("batch", payload, str(target))
                count += 1

        self.refresh_history_view()
        self.messagebox.showinfo("Batch export done", f"Generated {count} QR code(s) in {output_dir}")

    def _set_tool_output(self, text: str) -> None:
        self.tool_output.delete("1.0", "end")
        self.tool_output.insert("1.0", text)

    def _tool_text(self) -> str:
        return self.tool_input.get("1.0", "end").strip()

    def base64_encode(self) -> None:
        raw = self._tool_text().encode("utf-8")
        self._set_tool_output(base64.b64encode(raw).decode("utf-8"))

    def base64_decode(self) -> None:
        try:
            decoded = base64.b64decode(self._tool_text()).decode("utf-8")
        except Exception as exc:
            self.messagebox.showerror("Decode error", str(exc))
            return
        self._set_tool_output(decoded)

    def url_encode(self) -> None:
        self._set_tool_output(quote_plus(self._tool_text()))

    def url_decode(self) -> None:
        self._set_tool_output(unquote_plus(self._tool_text()))

    def sha256_hash(self) -> None:
        digest = hashlib.sha256(self._tool_text().encode("utf-8")).hexdigest()
        self._set_tool_output(digest)

    def _record_history(self, mode: str, payload: str, output_file: str) -> None:
        item = HistoryItem(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            mode=mode,
            payload=payload,
            output_file=output_file,
        )
        self.history.append(item)
        HISTORY_FILE.write_text(json.dumps([x.__dict__ for x in self.history], indent=2), encoding="utf-8")
        self.refresh_history_view()

    def _load_history(self) -> None:
        if HISTORY_FILE.exists():
            try:
                rows = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                self.history = [HistoryItem(**row) for row in rows]
            except Exception:
                self.history = []
        self.refresh_history_view()

    def refresh_history_view(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for item in reversed(self.history[-500:]):
            self.history_tree.insert("", "end", values=(item.timestamp, item.mode, item.output_file))

    def clear_history(self) -> None:
        if not self.messagebox.askyesno("Confirm", "Clear saved history?"):
            return
        self.history = []
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        self.refresh_history_view()


def run_doctor() -> int:
    checks = {
        "tkinter": importlib.util.find_spec("tkinter") is not None and importlib.util.find_spec("_tkinter") is not None,
        "qrcode": importlib.util.find_spec("qrcode") is not None,
        "Pillow": importlib.util.find_spec("PIL") is not None,
    }
    print("Dependency doctor report:")
    for name, ok in checks.items():
        print(f"- {name}: {'OK' if ok else 'MISSING'}")
    if checks["tkinter"]:
        print("UI should be launchable.")
    else:
        print("Tkinter missing: install a Python build with Tk support.")
        print("macOS tip: python.org installer includes Tk. Homebrew Python may need a Tk-enabled rebuild.")
    return 0 if all(checks.values()) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Modern QR Studio")
    parser.add_argument("--doctor", action="store_true", help="Check whether tkinter and optional dependencies are installed")
    args = parser.parse_args(argv)

    if args.doctor:
        return run_doctor()

    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
        from tkinter.scrolledtext import ScrolledText
    except Exception as exc:
        print("Cannot launch UI because tkinter is not available in this Python environment.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        print("Run `python main.py --doctor` for a full dependency report.", file=sys.stderr)
        return 1

    try:
        root = tk.Tk()
    except Exception as exc:
        print("Cannot launch UI in this environment.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return 1
    app = ModernQRStudio(root, tk, ttk, filedialog, messagebox, ScrolledText)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
