"""PDF and document reader — extract text from PDF, DOCX files."""

import os, subprocess

def _check_import(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def read_pdf(args, work_dir=None):
    """Extract text from PDF file."""
    path = args.get("path", "")
    pages = args.get("pages", "")

    if not path or not os.path.exists(path):
        return f"Error: PDF file not found: {path}"

    # Try PyMuPDF (fitz) first
    try:
        import fitz
        doc = fitz.open(path)
        total = doc.page_count
        if pages:
            if "-" in str(pages):
                start, end = map(int, str(pages).split("-"))
                page_range = range(start - 1, min(end, total))
            else:
                page_nums = [int(p) - 1 for p in str(pages).split(",")]
                page_range = [p for p in page_nums if 0 <= p < total]
        else:
            page_range = range(min(total, 20))

        text_parts = []
        for i in page_range:
            page = doc[i]
            text_parts.append(f"--- Page {i + 1} ---\n{page.get_text()}")
        doc.close()

        result = "\n\n".join(text_parts)
        if len(result) > 15000:
            result = result[:15000] + f"\n\n... (truncated, showing {len(page_range)} of {total} pages)"
        return result
    except ImportError:
        pass

    # Try pdftotext (poppler)
    try:
        cmd = ["pdftotext", "-layout", path, "-"]
        if pages:
            cmd = ["pdftotext", "-f", str(pages.split("-")[0]), "-l", str(pages.split("-")[-1] if "-" in str(pages) else pages), "-layout", path, "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            text = result.stdout
            if len(text) > 15000:
                text = text[:15000] + "\n\n... (truncated)"
            return text
        return f"Error: pdftotext failed: {result.stderr}"
    except FileNotFoundError:
        pass

    return "Error: No PDF reader available. Install PyMuPDF (pip install pymupdf) or poppler (apt install poppler-utils)."


def read_docx(args, work_dir=None):
    """Extract text from DOCX file."""
    path = args.get("path", "")

    if not path or not os.path.exists(path):
        return f"Error: DOCX file not found: {path}"

    try:
        from docx import Document
        doc = Document(path)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        result = "\n".join(text_parts)
        if len(result) > 15000:
            result = result[:15000] + "\n\n... (truncated)"
        return result
    except ImportError:
        return "Error: python-docx not installed. Install with: pip install python-docx"
    except Exception as e:
        return f"Error reading DOCX: {e}"


def read_document(args, work_dir=None):
    """Read a document file (auto-detect format)."""
    path = args.get("path", "")
    if not path:
        return "Error: No file path provided"

    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return read_pdf(args, work_dir)
    elif ext in (".docx", ".doc"):
        return read_docx(args, work_dir)
    elif ext == ".txt":
        with open(path, errors="replace") as f:
            return f.read()[:15000]
    elif ext == ".rtf":
        try:
            from striprtf.striprtf import rtf_to_text
            with open(path, errors="replace") as f:
                return rtf_to_text(f.read())[:15000]
        except ImportError:
            return "Error: striprtf not installed. Install with: pip install striprtf"
    return f"Error: Unsupported document format: {ext}"


TOOL_NAMES = {"read_document"}

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Read and extract text from document files: PDF, DOCX, TXT, RTF. Supports page ranges for PDFs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the document file"},
                    "pages": {"type": "string", "description": "Page range for PDF (e.g., '1-5', '1,3,5'). Default: first 20 pages."}
                },
                "required": ["path"]
            }
        }
    }
]


def execute(name, args, work_dir=None, bot=None):
    return read_document(args, work_dir)
