# Modern QR Studio (Tkinter)

A refreshed and significantly expanded desktop toolkit built with Python + Tkinter.

## What's new compared to the legacy app

- Modernized UI using `ttk` + tabbed workflow.
- Advanced QR generation with:
  - error-correction level (`L/M/Q/H`)
  - foreground/background color customization
  - box size + border controls
  - instant preview pane
- Batch QR generation from CSV.
- Built-in utility tools for text workflows:
  - Base64 encode/decode
  - URL encode/decode
  - SHA256 hashing
- Persistent export history saved in `history.json`.
- Better error handling and dependency checks.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

If the UI cannot start, run:

```bash
python main.py --doctor
```

This checks whether `tkinter`, `qrcode`, and `Pillow` are available. If `_tkinter` is missing on your machine, install a Python build that includes Tk support and re-run the doctor command.

## Batch CSV format

CSV rows:

```text
payload,optional_filename
https://example.com,example_site
hello world,
```

- Column 1 is required payload text.
- Column 2 is optional output file name (without extension).

## Notes

- Exports are PNG by default.
- History is stored locally in `history.json`.
