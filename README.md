# PDF Redactor

A pdf viewer to redact/censor information in PDF files using a black highlighter.

## Features

- **Open PDFs**: Load and view PDF files
- **Black Highlighter**: Draw black rectangles by dragging the mouse over content you want to redact
- **Save PDFs**: Save the redacted PDF as a new file (redactions are permanent)
- **Zoom**: Zoom in/out for precision
- **Intuitive Interface**: Menus and keyboard shortcuts for common operations

## Requirements

- Python 3.10 or higher
- uv (package manager)

## Installation

1. Clone or download this repository:
```bash
cd redact-pdf
```

2. Dependencies are already configured with uv. To install:
```bash
uv sync
```

## Usage

### Run the application

```bash
uv run python -m redact_pdf.main
```

Or alternatively:

```bash
uv run python src/redact_pdf/main.py
```

### How to redact a PDF
Use the mouse to draw a rectangle over the data you want to redact. Then, save the document.

### Keyboard shortcuts

| Action | Shortcut |
|--------|----------|
| Open PDF | `Ctrl+O` |
| Save as | `Ctrl+S` |
| Exit | `Ctrl+Q` |
| Zoom in | `Ctrl++` |
| Zoom out | `Ctrl+-` |
| Fit to window | `Ctrl+0` |

## Project Structure

```
redact-pdf/
├── src/
│   └── redact_pdf/
│       ├── main.py                      # Entry point
│       ├── models/
│       │   └── pdf_document.py          # PyMuPDF model
│       ├── views/
│       │   ├── main_window.py           # Main window
│       │   └── pdf_viewer.py            # PDF viewer with drawing
│       └── controllers/
│           └── redaction_controller.py  # Redaction logic
├── pyproject.toml                       # Project configuration
└── README.md                            # This file
```

## Technologies

- **Python**: Programming language
- **uv**: Package and virtual environment manager
- **PyQt6**: GUI framework
- **PyMuPDF (fitz)**: Library for PDF rendering and manipulation

## Limitations (MVP)

- The document is visualized pixelated
- Only shows the first page of the PDF
- No undo/redo functionality
- No preview before saving
- No text search for auto-redaction

## License

Free to use.
