"""Database & data processing tools."""

import json, csv, sqlite3

TOOL_DEFS = [
    {"type": "function", "function": {"name": "db_connect", "description": "Connect to a SQLite database. Creates if not exists. Returns connection info.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to SQLite database file"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "db_query", "description": "Execute SQL query on a SQLite database. Returns rows as text.", "parameters": {"type": "object", "properties": {"db_path": {"type": "string", "description": "Path to SQLite database"}, "sql": {"type": "string", "description": "SQL query to execute"}, "params": {"type": "array", "items": {"type": "string"}, "description": "Query parameters for parameterized queries"}}, "required": ["db_path", "sql"]}}},
    {"type": "function", "function": {"name": "db_schema", "description": "Show all tables and their schema in a SQLite database.", "parameters": {"type": "object", "properties": {"db_path": {"type": "string", "description": "Path to SQLite database"}}, "required": ["db_path"]}}},
    {"type": "function", "function": {"name": "db_dump", "description": "Export database table to CSV or JSON file.", "parameters": {"type": "object", "properties": {"db_path": {"type": "string", "description": "Path to SQLite database"}, "table": {"type": "string", "description": "Table name to export"}, "output": {"type": "string", "description": "Output file path (.csv or .json)"}, "format": {"type": "string", "enum": ["csv", "json"], "description": "Output format"}}, "required": ["db_path", "table", "output"]}}},
    {"type": "function", "function": {"name": "csv_read", "description": "Read and parse a CSV file. Returns rows as text.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to CSV file"}, "limit": {"type": "integer", "description": "Max rows to return (default 100)"}, "delimiter": {"type": "string", "description": "Column delimiter (default comma)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "csv_write", "description": "Write data to a CSV file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Output file path"}, "headers": {"type": "array", "items": {"type": "string"}, "description": "Column headers"}, "rows": {"type": "array", "items": {"type": "array"}, "description": "Data rows"}}, "required": ["path", "headers", "rows"]}}},
    {"type": "function", "function": {"name": "json_read", "description": "Read and parse a JSON file. Returns the content.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to JSON file"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "json_write", "description": "Write data to a JSON file with pretty formatting.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Output file path"}, "data": {"type": "string", "description": "JSON data as string"}, "indent": {"type": "integer", "description": "Indentation spaces (default 2)"}}, "required": ["path", "data"]}}},
    {"type": "function", "function": {"name": "json_query", "description": "Query JSON data using Python expressions. Supports filtering, mapping, selecting keys.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to JSON file"}, "query": {"type": "string", "description": "Python expression to filter (e.g. '[x for x in data if x[\"age\"] > 25]')"}}, "required": ["path", "query"]}}},
    {"type": "function", "function": {"name": "json_merge", "description": "Merge multiple JSON files into one.", "parameters": {"type": "object", "properties": {"files": {"type": "array", "items": {"type": "string"}, "description": "JSON files to merge"}, "output": {"type": "string", "description": "Output file path"}, "strategy": {"type": "string", "enum": ["update", "replace", "append"], "description": "Merge strategy (default update)"}}, "required": ["files", "output"]}}},
    {"type": "function", "function": {"name": "json_to_csv", "description": "Convert JSON array to CSV file.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Path to JSON file"}, "output": {"type": "string", "description": "Path to output CSV"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "csv_to_json", "description": "Convert CSV file to JSON array.", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "Path to CSV file"}, "output": {"type": "string", "description": "Path to output JSON"}}, "required": ["input", "output"]}}},
    {"type": "function", "function": {"name": "yaml_read", "description": "Read and parse a YAML file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to YAML file"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "yaml_write", "description": "Write data to a YAML file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Output file path"}, "data": {"type": "string", "description": "Data as JSON string to convert to YAML"}}, "required": ["path", "data"]}}},
    {"type": "function", "function": {"name": "data_sample", "description": "Get a random sample of rows from a CSV or JSON file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to data file"}, "count": {"type": "integer", "description": "Number of samples (default 5)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "data_stats", "description": "Get basic statistics (count, min, max, mean, median) for numeric columns in CSV.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to CSV file"}, "column": {"type": "string", "description": "Column name (omit for all numeric columns)"}}, "required": ["path"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "db_connect":
            path = args["path"]
            conn = sqlite3.connect(path)
            conn.close()
            return f"Connected to {path} (SQLite {sqlite3.sqlite_version})"

        elif name == "db_query":
            conn = sqlite3.connect(args["db_path"])
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            params = tuple(args.get("params", []))
            cur.execute(args["sql"], params)
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                lines = ["\t".join(cols)]
                for r in rows[:500]:
                    lines.append("\t".join(str(v) for v in r))
                conn.close()
                return "\n".join(lines) or "(empty result)"
            else:
                conn.commit()
                conn.close()
                return f"OK — {cur.rowcount} rows affected"

        elif name == "db_schema":
            conn = sqlite3.connect(args["db_path"])
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cur.fetchall()
            lines = []
            for t in tables:
                cur.execute(f"PRAGMA table_info('{t[0]}')")
                cols = cur.fetchall()
                lines.append(f"\n[{t[0]}]")
                for c in cols:
                    lines.append(f"  {c[1]} ({c[2]}){' PRIMARY KEY' if c[5] else ''}")
            conn.close()
            return "\n".join(lines) or "(no tables)"

        elif name == "db_dump":
            conn = sqlite3.connect(args["db_path"])
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {args['table']}")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            fmt = args.get("format", "csv")
            if fmt == "json":
                data = [dict(r) for r in rows]
                with open(args["output"], "w") as f:
                    json.dump(data, f, indent=2)
            else:
                with open(args["output"], "w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(cols)
                    w.writerows(rows)
            conn.close()
            return f"Exported {len(rows)} rows to {args['output']}"

        elif name == "csv_read":
            delimiter = args.get("delimiter", ",")
            limit = args.get("limit", 100)
            with open(args["path"], newline="") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = [next(reader)]
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    rows.append(row)
            return "\n".join("\t".join(r) for r in rows)

        elif name == "csv_write":
            with open(args["path"], "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(args["headers"])
                w.writerows(args["rows"])
            return f"Wrote {len(args['rows'])} rows to {args['path']}"

        elif name == "json_read":
            with open(args["path"]) as f:
                data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)[:5000]

        elif name == "json_write":
            data = json.loads(args["data"])
            indent = args.get("indent", 2)
            with open(args["path"], "w") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return f"Written to {args['path']}"

        elif name == "json_query":
            with open(args["path"]) as f:
                data = json.load(f)
            result = eval(args["query"], {"data": data, "__builtins__": {}})
            return json.dumps(result, indent=2, ensure_ascii=False)[:5000]

        elif name == "json_merge":
            merged = {}
            strategy = args.get("strategy", "update")
            for fp in args["files"]:
                with open(fp) as f:
                    d = json.load(f)
                if strategy == "replace":
                    merged = d
                elif strategy == "append":
                    if isinstance(merged, list):
                        merged.extend(d if isinstance(d, list) else [d])
                    else:
                        merged.update(d)
                else:
                    merged.update(d if isinstance(d, dict) else {})
            with open(args["output"], "w") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
            return f"Merged {len(args['files'])} files into {args['output']}"

        elif name == "json_to_csv":
            with open(args["input"]) as f:
                data = json.load(f)
            if not data:
                return "Empty JSON array"
            keys = list(data[0].keys()) if isinstance(data[0], dict) else []
            with open(args["output"], "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                w.writerows(data)
            return f"Converted {len(data)} items to {args['output']}"

        elif name == "csv_to_json":
            with open(args["input"], newline="") as f:
                data = list(csv.DictReader(f))
            with open(args["output"], "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return f"Converted {len(data)} rows to {args['output']}"

        elif name == "yaml_read":
            try:
                import yaml
            except ImportError:
                return "Error: pyyaml not installed. Run: pip install pyyaml"
            with open(args["path"]) as f:
                data = yaml.safe_load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)[:5000]

        elif name == "yaml_write":
            try:
                import yaml
            except ImportError:
                return "Error: pyyaml not installed. Run: pip install pyyaml"
            data = json.loads(args["data"])
            with open(args["path"], "w") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            return f"Written to {args['path']}"

        elif name == "data_sample":
            import random
            path = args["path"]
            count = args.get("count", 5)
            if path.endswith(".json"):
                with open(path) as f:
                    data = json.load(f)
                sample = random.sample(data, min(count, len(data)))
                return json.dumps(sample, indent=2, ensure_ascii=False)
            else:
                with open(path, newline="") as f:
                    reader = list(csv.reader(f))
                header = reader[0]
                sample = random.sample(reader[1:], min(count, len(reader) - 1))
                return "\n".join("\t".join([header[0]] + ["..."]) for _ in []) or "\n".join("\t".join(r) for r in [header] + sample)

        elif name == "data_stats":
            import statistics
            path = args["path"]
            column = args.get("column")
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            cols = column or list(rows[0].keys()) if rows else []
            if column:
                cols = [column]
            lines = []
            for c in cols:
                vals = []
                for r in rows:
                    try:
                        vals.append(float(r[c]))
                    except (ValueError, TypeError, KeyError):
                        continue
                if vals:
                    lines.append(f"{c}: count={len(vals)} min={min(vals):.2f} max={max(vals):.2f} mean={statistics.mean(vals):.2f} median={statistics.median(vals):.2f} stdev={statistics.stdev(vals):.2f}" if len(vals) > 1 else f"{c}: count={len(vals)} min={min(vals):.2f} max={max(vals):.2f}")
            return "\n".join(lines) or "(no numeric columns found)"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
