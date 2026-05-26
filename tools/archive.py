"""Archive and compression tools."""

import subprocess, os, zipfile, tarfile, gzip, shutil

TOOL_DEFS = [
    {"type": "function", "function": {"name": "zip_create", "description": "Create a ZIP archive from files or directories.", "parameters": {"type": "object", "properties": {"output": {"type": "string", "description": "Output ZIP file path"}, "sources": {"type": "array", "items": {"type": "string"}, "description": "Files or directories to include"}, "exclude": {"type": "string", "description": "Glob patterns to exclude (e.g. '*.pyc,__pycache__')"}}, "required": ["output", "sources"]}}},
    {"type": "function", "function": {"name": "zip_extract", "description": "Extract a ZIP archive.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "ZIP file path"}, "output": {"type": "string", "description": "Extract to directory (default: current dir)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "zip_list", "description": "List contents of a ZIP archive without extracting.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "ZIP file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "tar_create", "description": "Create a tar.gz archive.", "parameters": {"type": "object", "properties": {"output": {"type": "string", "description": "Output tar.gz file path"}, "sources": {"type": "array", "items": {"type": "string"}, "description": "Files or directories to include"}, "exclude": {"type": "string", "description": "Patterns to exclude"}}, "required": ["output", "sources"]}}},
    {"type": "function", "function": {"name": "tar_extract", "description": "Extract a tar.gz archive.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "tar.gz file path"}, "output": {"type": "string", "description": "Extract to directory"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "tar_list", "description": "List contents of a tar.gz archive.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "tar.gz file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "gzip_compress", "description": "Compress a file using gzip.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input file path"}, "output": {"type": "string", "description": "Output .gz file path (default: input.gz)"}}, "required": ["input"]}}},
    {"type": "function", "function": {"name": "gzip_decompress", "description": "Decompress a gzip file.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Input .gz file path"}, "output": {"type": "string", "description": "Output file path"}}, "required": ["input"]}}},
    {"type": "function", "function": {"name": "7z_create", "description": "Create a 7z archive (requires p7zip).", "parameters": {"type": "object", "properties": {"output": {"type": "string", "description": "Output .7z file path"}, "sources": {"type": "array", "items": {"type": "string"}, "description": "Files or directories to include"}}, "required": ["output", "sources"]}}},
    {"type": "function", "function": {"name": "7z_extract", "description": "Extract a 7z archive.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "7z file path"}, "output": {"type": "string", "description": "Extract to directory"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "archive_info", "description": "Get info about any archive (ZIP, tar.gz, 7z) — type, size, file count.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Archive file path"}}, "required": ["path"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "zip_create":
            output = args["output"]
            sources = args["sources"]
            exclude = set(args.get("exclude", "").split(",")) if args.get("exclude") else set()
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
                for src in sources:
                    if os.path.isfile(src):
                        zf.write(src, os.path.basename(src))
                    elif os.path.isdir(src):
                        for root, dirs, files in os.walk(src):
                            dirs[:] = [d for d in dirs if d not in exclude]
                            for f in files:
                                if f not in exclude:
                                    fp = os.path.join(root, f)
                                    arcname = os.path.relpath(fp, os.path.dirname(src))
                                    zf.write(fp, arcname)
            return f"Created {output} ({os.path.getsize(output)} bytes)"

        elif name == "zip_extract":
            output = args.get("output", ".")
            with zipfile.ZipFile(args["path"], "r") as zf:
                zf.extractall(output)
                return f"Extracted {len(zf.namelist())} files to {output}"

        elif name == "zip_list":
            with zipfile.ZipFile(args["path"], "r") as zf:
                lines = []
                for info in zf.infolist():
                    lines.append(f"  {info.filename} ({info.file_size} bytes)")
                return f"Files ({len(lines)}):\n" + "\n".join(lines[:100])

        elif name == "tar_create":
            output = args["output"]
            sources = args["sources"]
            with tarfile.open(output, "w:gz") as tf:
                for src in sources:
                    tf.add(src, arcname=os.path.basename(src))
            return f"Created {output} ({os.path.getsize(output)} bytes)"

        elif name == "tar_extract":
            output = args.get("output", ".")
            with tarfile.open(args["path"], "r:gz") as tf:
                tf.extractall(output)
                return f"Extracted to {output}"

        elif name == "tar_list":
            with tarfile.open(args["path"], "r:gz") as tf:
                lines = [f"  {m.name} ({m.size} bytes)" for m in tf.getmembers()]
                return f"Files ({len(lines)}):\n" + "\n".join(lines[:100])

        elif name == "gzip_compress":
            output = args.get("output", args["input"] + ".gz")
            with open(args["input"], "rb") as f_in:
                with gzip.open(output, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            orig = os.path.getsize(args["input"])
            comp = os.path.getsize(output)
            return f"Compressed: {output}\nOriginal: {orig} bytes\nCompressed: {comp} bytes\nRatio: {comp * 100 // orig}%"

        elif name == "gzip_decompress":
            output = args.get("output", args["input"].rstrip(".gz"))
            with gzip.open(args["input"], "rb") as f_in:
                with open(output, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return f"Decompressed to {output} ({os.path.getsize(output)} bytes)"

        elif name == "7z_create":
            output = args["output"]
            sources = " ".join(args["sources"])
            r = subprocess.run(["7z", "a", output] + args["sources"], capture_output=True, text=True, timeout=60)
            return r.stdout[-2000:] or r.stderr[-2000:]

        elif name == "7z_extract":
            output = args.get("output", ".")
            r = subprocess.run(["7z", "x", args["path"], f"-o{output}"], capture_output=True, text=True, timeout=60)
            return r.stdout[-2000:] or r.stderr[-2000:]

        elif name == "archive_info":
            path = args["path"]
            size = os.path.getsize(path)
            if path.endswith(".zip"):
                with zipfile.ZipFile(path, "r") as zf:
                    count = len(zf.namelist())
                return f"Type: ZIP\nSize: {size} bytes\nFiles: {count}"
            elif path.endswith((".tar.gz", ".tgz")):
                with tarfile.open(path, "r:gz") as tf:
                    count = len(tf.getmembers())
                return f"Type: tar.gz\nSize: {size} bytes\nFiles: {count}"
            elif path.endswith(".7z"):
                r = subprocess.run(["7z", "l", path], capture_output=True, text=True, timeout=10)
                return f"Type: 7z\nSize: {size} bytes\n{r.stdout[-1000:]}"
            elif path.endswith(".gz"):
                return f"Type: gzip\nSize: {size} bytes"
            return f"Type: unknown\nSize: {size} bytes"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
