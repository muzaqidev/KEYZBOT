"""PDF manipulation tools — read, merge, split, watermark, convert, extract."""

import subprocess, os

TOOL_DEFS = [
    {"type": "function", "function": {"name": "pdf_read", "description": "Read text content from a PDF file. Supports page ranges.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "PDF file path"}, "pages": {"type": "string", "description": "Page range (e.g. '1-5', '3', '1,3,5')"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "pdf_info", "description": "Get PDF metadata: page count, title, author, creation date, file size.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "PDF file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "pdf_merge", "description": "Merge multiple PDF files into one.", "parameters": {"type": "object", "properties": {"files": {"type": "array", "items": {"type": "string"}, "description": "PDF files to merge (in order)"}, "output": {"type": "string", "description": "Output PDF path"}}, "required": ["files", "output"]}}},
    {"type": "function", "function": {"name": "pdf_split", "description": "Split a PDF into individual pages or page ranges.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Input PDF path"}, "output_dir": {"type": "string", "description": "Output directory"}, "pages": {"type": "string", "description": "Page ranges to extract (e.g. '1-3,5,7-9'). Omit for all pages."}}, "required": ["path", "output_dir"]}}},
    {"type": "function", "function": {"name": "pdf_extract_pages", "description": "Extract specific pages from a PDF into a new file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Input PDF path"}, "pages": {"type": "string", "description": "Pages to extract (e.g. '1-5,10')"}, "output": {"type": "string", "description": "Output PDF path"}}, "required": ["path", "pages", "output"]}}},
    {"type": "function", "function": {"name": "pdf_remove_pages", "description": "Remove specific pages from a PDF.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Input PDF path"}, "pages": {"type": "string", "description": "Pages to remove (e.g. '2,5,8')"}, "output": {"type": "string", "description": "Output PDF path"}}, "required": ["path", "pages", "output"]}}},
    {"type": "function", "function": {"name": "pdf_rotate", "description": "Rotate pages in a PDF.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Input PDF path"}, "pages": {"type": "string", "description": "Pages to rotate (e.g. '1-3' or 'all')"}, "degrees": {"type": "integer", "enum": [90, 180, 270], "description": "Rotation degrees"}, "output": {"type": "string", "description": "Output PDF path"}}, "required": ["path", "degrees", "output"]}}},
    {"type": "function", "function": {"name": "pdf_watermark", "description": "Add a text watermark to PDF pages.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Input PDF path"}, "text": {"type": "string", "description": "Watermark text"}, "output": {"type": "string", "description": "Output PDF path"}, "opacity": {"type": "number", "description": "Opacity 0-1 (default 0.3)"}, "font_size": {"type": "integer", "description": "Font size (default 50)"}}, "required": ["path", "text", "output"]}}},
    {"type": "function", "function": {"name": "pdf_images", "description": "Extract all images from a PDF file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "PDF file path"}, "output_dir": {"type": "string", "description": "Directory to save images"}}, "required": ["path", "output_dir"]}}},
    {"type": "function", "function": {"name": "pdf_to_text", "description": "Convert PDF to plain text file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "PDF file path"}, "output": {"type": "string", "description": "Output text file path"}}, "required": ["path", "output"]}}},
    {"type": "function", "function": {"name": "text_to_pdf", "description": "Convert a text file to PDF.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Text file path"}, "output": {"type": "string", "description": "Output PDF path"}, "font_size": {"type": "integer", "description": "Font size (default 12)"}}, "required": ["path", "output"]}}},
    {"type": "function", "function": {"name": "pdf_page_count", "description": "Get the number of pages in a PDF.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "PDF file path"}}, "required": ["path"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def _get_lib():
    """Try to import PyPDF2, fallback to pypdf."""
    try:
        import PyPDF2
        return PyPDF2
    except ImportError:
        try:
            import pypdf
            return pypdf
        except ImportError:
            return None


def execute(name, args, work_dir=None):
    try:
        if name == "pdf_read":
            lib = _get_lib()
            if not lib:
                # Fallback to pdftotext
                r = subprocess.run(["pdftotext", args["path"], "-"], capture_output=True, text=True, timeout=30)
                return r.stdout[:8000] or r.stderr or "(empty)"
            reader = lib.PdfReader(args["path"])
            pages_str = args.get("pages", "")
            if pages_str:
                page_nums = _parse_pages(pages_str, len(reader.pages))
            else:
                page_nums = range(len(reader.pages))
            text_parts = []
            for i in page_nums:
                text = reader.pages[i].extract_text() or ""
                text_parts.append(f"--- Page {i+1} ---\n{text}")
            return "\n".join(text_parts)[:8000]

        elif name == "pdf_info":
            lib = _get_lib()
            if not lib:
                r = subprocess.run(["pdfinfo", args["path"]], capture_output=True, text=True, timeout=10)
                return r.stdout or r.stderr
            reader = lib.PdfReader(args["path"])
            meta = reader.metadata
            lines = [f"Pages: {len(reader.pages)}"]
            if meta:
                for k, v in meta.items():
                    if v:
                        lines.append(f"{k}: {v}")
            lines.append(f"Size: {os.path.getsize(args['path'])} bytes")
            return "\n".join(lines)

        elif name == "pdf_merge":
            lib = _get_lib()
            if not lib:
                return "Error: PyPDF2/pypdf not installed"
            writer = lib.PdfWriter()
            for fp in args["files"]:
                reader = lib.PdfReader(fp)
                for page in reader.pages:
                    writer.add_page(page)
            with open(args["output"], "wb") as f:
                writer.write(f)
            return f"Merged {len(args['files'])} PDFs into {args['output']}"

        elif name == "pdf_split":
            lib = _get_lib()
            if not lib:
                return "Error: PyPDF2/pypdf not installed"
            reader = lib.PdfReader(args["path"])
            output_dir = args["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            pages_str = args.get("pages", "")
            if pages_str:
                page_nums = _parse_pages(pages_str, len(reader.pages))
            else:
                page_nums = range(len(reader.pages))
            created = []
            for i in page_nums:
                writer = lib.PdfWriter()
                writer.add_page(reader.pages[i])
                out = os.path.join(output_dir, f"page_{i+1}.pdf")
                with open(out, "wb") as f:
                    writer.write(f)
                created.append(out)
            return f"Split into {len(created)} files in {output_dir}"

        elif name == "pdf_extract_pages":
            lib = _get_lib()
            if not lib:
                return "Error: PyPDF2/pypdf not installed"
            reader = lib.PdfReader(args["path"])
            writer = lib.PdfWriter()
            page_nums = _parse_pages(args["pages"], len(reader.pages))
            for i in page_nums:
                writer.add_page(reader.pages[i])
            with open(args["output"], "wb") as f:
                writer.write(f)
            return f"Extracted {len(page_nums)} pages to {args['output']}"

        elif name == "pdf_remove_pages":
            lib = _get_lib()
            if not lib:
                return "Error: PyPDF2/pypdf not installed"
            reader = lib.PdfReader(args["path"])
            remove = set(_parse_pages(args["pages"], len(reader.pages)))
            writer = lib.PdfWriter()
            for i, page in enumerate(reader.pages):
                if i not in remove:
                    writer.add_page(page)
            with open(args["output"], "wb") as f:
                writer.write(f)
            return f"Removed {len(remove)} pages, saved to {args['output']}"

        elif name == "pdf_rotate":
            lib = _get_lib()
            if not lib:
                return "Error: PyPDF2/pypdf not installed"
            reader = lib.PdfReader(args["path"])
            writer = lib.PdfWriter()
            pages_str = args.get("pages", "all")
            degrees = args["degrees"]
            if pages_str == "all":
                rotate_set = set(range(len(reader.pages)))
            else:
                rotate_set = set(_parse_pages(pages_str, len(reader.pages)))
            for i, page in enumerate(reader.pages):
                if i in rotate_set:
                    page.rotate(degrees)
                writer.add_page(page)
            with open(args["output"], "wb") as f:
                writer.write(f)
            return f"Rotated {len(rotate_set)} pages by {degrees} degrees"

        elif name == "pdf_watermark":
            lib = _get_lib()
            if not lib:
                return "Error: PyPDF2/pypdf not installed"
            # Create watermark PDF
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.pagesizes import letter
            import io
            packet = io.BytesIO()
            c = rl_canvas.Canvas(packet, pagesize=letter)
            c.setFont("Helvetica", args.get("font_size", 50))
            c.setFillAlpha(args.get("opacity", 0.3))
            c.saveState()
            c.translate(letter[0]/2, letter[1]/2)
            c.rotate(45)
            c.drawCentredString(0, 0, args["text"])
            c.restoreState()
            c.save()
            packet.seek(0)
            wm_reader = lib.PdfReader(packet)
            wm_page = wm_reader.pages[0]
            reader = lib.PdfReader(args["path"])
            writer = lib.PdfWriter()
            for page in reader.pages:
                page.merge_page(wm_page)
                writer.add_page(page)
            with open(args["output"], "wb") as f:
                writer.write(f)
            return f"Watermark added to {len(reader.pages)} pages"

        elif name == "pdf_images":
            lib = _get_lib()
            if not lib:
                return "Error: PyPDF2/pypdf not installed"
            reader = lib.PdfReader(args["path"])
            output_dir = args["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            count = 0
            for i, page in enumerate(reader.pages):
                if hasattr(page, 'images'):
                    for j, img in enumerate(page.images):
                        out = os.path.join(output_dir, f"page{i+1}_img{j+1}_{img.name}")
                        with open(out, "wb") as f:
                            f.write(img.data)
                        count += 1
            return f"Extracted {count} images to {output_dir}"

        elif name == "pdf_to_text":
            r = subprocess.run(["pdftotext", args["path"], args["output"]], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return f"Text saved to {args['output']}"
            return f"Error: {r.stderr}"

        elif name == "text_to_pdf":
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            font_size = args.get("font_size", 12)
            with open(args["path"]) as f:
                lines = f.readlines()
            c = canvas.Canvas(args["output"], pagesize=letter)
            c.setFont("Helvetica", font_size)
            y = letter[1] - 50
            for line in lines:
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", font_size)
                    y = letter[1] - 50
                c.drawString(50, y, line.rstrip()[:100])
                y -= font_size + 4
            c.save()
            return f"PDF saved to {args['output']}"

        elif name == "pdf_page_count":
            lib = _get_lib()
            if not lib:
                r = subprocess.run(["pdfinfo", args["path"]], capture_output=True, text=True, timeout=10)
                for line in r.stdout.split("\n"):
                    if "Pages:" in line:
                        return line.strip()
                return "Error: cannot read PDF"
            reader = lib.PdfReader(args["path"])
            return f"Pages: {len(reader.pages)}"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"


def _parse_pages(pages_str, max_pages):
    """Parse page range string like '1-3,5,7-9' into list of 0-indexed page numbers."""
    result = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            result.extend(range(int(start) - 1, min(int(end), max_pages)))
        else:
            n = int(part) - 1
            if 0 <= n < max_pages:
                result.append(n)
    return result
