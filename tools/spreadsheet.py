"""Spreadsheet tools — read, write, calculate, filter CSV/Excel files."""

import csv, json, os, io

TOOL_DEFS = [
    {"type": "function", "function": {"name": "sheet_read", "description": "Read a spreadsheet (CSV/XLSX) and return rows as structured data.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path (.csv or .xlsx)"}, "sheet": {"type": "string", "description": "Sheet name for XLSX (default first)"}, "limit": {"type": "integer", "description": "Max rows (default 100)"}, "offset": {"type": "integer", "description": "Skip N rows (default 0)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "sheet_write", "description": "Write data to a CSV file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Output file path"}, "headers": {"type": "array", "items": {"type": "string"}, "description": "Column headers"}, "rows": {"type": "array", "items": {"type": "array"}, "description": "Data rows"}}, "required": ["path", "headers", "rows"]}}},
    {"type": "function", "function": {"name": "sheet_filter", "description": "Filter spreadsheet rows by column value.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "column": {"type": "string", "description": "Column name to filter"}, "operator": {"type": "string", "enum": ["equals", "contains", "gt", "lt", "gte", "lte", "not_empty", "regex"], "description": "Filter operator"}, "value": {"type": "string", "description": "Value to compare against"}, "limit": {"type": "integer", "description": "Max results (default 100)"}}, "required": ["path", "column", "operator"]}}},
    {"type": "function", "function": {"name": "sheet_sort", "description": "Sort spreadsheet by column.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "column": {"type": "string", "description": "Column to sort by"}, "reverse": {"type": "boolean", "description": "Descending order (default false)"}, "output": {"type": "string", "description": "Output file path"}}, "required": ["path", "column"]}}},
    {"type": "function", "function": {"name": "sheet_aggregate", "description": "Aggregate spreadsheet data: sum, avg, min, max, count per group.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "group_by": {"type": "string", "description": "Column to group by"}, "agg_column": {"type": "string", "description": "Column to aggregate"}, "function": {"type": "string", "enum": ["sum", "avg", "min", "max", "count"], "description": "Aggregation function"}}, "required": ["path", "group_by", "agg_column", "function"]}}},
    {"type": "function", "function": {"name": "sheet_pivot", "description": "Create a pivot table from spreadsheet data.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "index": {"type": "string", "description": "Column for rows"}, "columns": {"type": "string", "description": "Column for columns"}, "values": {"type": "string", "description": "Column for values"}, "aggfunc": {"type": "string", "enum": ["sum", "avg", "count"], "description": "Aggregation (default sum)"}}, "required": ["path", "index", "columns", "values"]}}},
    {"type": "function", "function": {"name": "sheet_columns", "description": "List all column names and their data types in a spreadsheet.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "sheet_row_count", "description": "Count total rows in a spreadsheet.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "sheet_find", "description": "Search for a value across all columns in a spreadsheet.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "search": {"type": "string", "description": "Value to search for"}, "case_sensitive": {"type": "boolean", "description": "Case sensitive (default false)"}}, "required": ["path", "search"]}}},
    {"type": "function", "function": {"name": "sheet_add_column", "description": "Add a new column to a spreadsheet with a formula or default value.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "name": {"type": "string", "description": "New column name"}, "formula": {"type": "string", "description": "Python expression using other columns (e.g. 'row[\"price\"] * row[\"qty\"]')"}, "default": {"type": "string", "description": "Default value (if no formula)"}, "output": {"type": "string", "description": "Output file path"}}, "required": ["path", "name", "output"]}}},
    {"type": "function", "function": {"name": "sheet_merge", "description": "Merge two spreadsheets by common column (like SQL join).", "parameters": {"type": "object", "properties": {"left": {"type": "string", "description": "Left spreadsheet path"}, "right": {"type": "string", "description": "Right spreadsheet path"}, "on": {"type": "string", "description": "Common column name"}, "how": {"type": "string", "enum": ["inner", "left", "right", "outer"], "description": "Join type (default inner)"}, "output": {"type": "string", "description": "Output file path"}}, "required": ["left", "right", "on", "output"]}}},
    {"type": "function", "function": {"name": "sheet_dedup", "description": "Remove duplicate rows from a spreadsheet.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "column": {"type": "string", "description": "Column to check for duplicates (omit for all)"}, "output": {"type": "string", "description": "Output file path"}}, "required": ["path", "output"]}}},
    {"type": "function", "function": {"name": "sheet_sample", "description": "Get a random sample of N rows from a spreadsheet.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Spreadsheet file path"}, "count": {"type": "integer", "description": "Number of rows (default 10)"}, "seed": {"type": "integer", "description": "Random seed for reproducibility"}}, "required": ["path"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def _read_csv(path, limit=1000, offset=0):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = []
        for i, row in enumerate(reader):
            if i < offset:
                continue
            if len(rows) >= limit:
                break
            rows.append(row)
    return headers, rows


def execute(name, args, work_dir=None):
    try:
        if name == "sheet_read":
            limit = args.get("limit", 100)
            offset = args.get("offset", 0)
            headers, rows = _read_csv(args["path"], limit, offset)
            lines = ["\t".join(headers)]
            for r in rows:
                lines.append("\t".join(str(r.get(h, "")) for h in headers))
            return "\n".join(lines) if lines else "(empty)"

        elif name == "sheet_write":
            with open(args["path"], "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(args["headers"])
                w.writerows(args["rows"])
            return f"Wrote {len(args['rows'])} rows to {args['path']}"

        elif name == "sheet_filter":
            headers, rows = _read_csv(args["path"], limit=10000)
            col = args["column"]
            op = args["operator"]
            val = args.get("value", "")
            limit = args.get("limit", 100)
            filtered = []
            import re
            for r in rows:
                cell = str(r.get(col, ""))
                match = False
                if op == "equals": match = cell == val
                elif op == "contains": match = val.lower() in cell.lower()
                elif op == "gt": match = float(cell) > float(val) if _is_num(cell) else False
                elif op == "lt": match = float(cell) < float(val) if _is_num(cell) else False
                elif op == "gte": match = float(cell) >= float(val) if _is_num(cell) else False
                elif op == "lte": match = float(cell) <= float(val) if _is_num(cell) else False
                elif op == "not_empty": match = bool(cell.strip())
                elif op == "regex": match = bool(re.search(val, cell))
                if match:
                    filtered.append(r)
                    if len(filtered) >= limit:
                        break
            lines = ["\t".join(headers)]
            for r in filtered:
                lines.append("\t".join(str(r.get(h, "")) for h in headers))
            return f"Found {len(filtered)} rows:\n" + "\n".join(lines)

        elif name == "sheet_sort":
            headers, rows = _read_csv(args["path"], limit=100000)
            col = args["column"]
            reverse = args.get("reverse", False)
            rows.sort(key=lambda r: r.get(col, ""), reverse=reverse)
            output = args.get("output", args["path"])
            with open(output, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                w.writerows(rows)
            return f"Sorted by {col}, saved to {output} ({len(rows)} rows)"

        elif name == "sheet_aggregate":
            headers, rows = _read_csv(args["path"], limit=100000)
            group_by = args["group_by"]
            agg_col = args["agg_column"]
            func = args["function"]
            groups = {}
            for r in rows:
                key = r.get(group_by, "")
                val = r.get(agg_col, "0")
                try:
                    val = float(val)
                except:
                    continue
                groups.setdefault(key, []).append(val)
            result = []
            for key, vals in sorted(groups.items()):
                if func == "sum": agg = sum(vals)
                elif func == "avg": agg = sum(vals) / len(vals)
                elif func == "min": agg = min(vals)
                elif func == "max": agg = max(vals)
                elif func == "count": agg = len(vals)
                else: agg = sum(vals)
                result.append(f"{key}\t{agg:.4g}")
            return f"{group_by}\t{func}({agg_col})\n" + "\n".join(result)

        elif name == "sheet_pivot":
            headers, rows = _read_csv(args["path"], limit=100000)
            idx = args["index"]
            col = args["columns"]
            val = args["values"]
            aggfunc = args.get("aggfunc", "sum")
            pivot = {}
            all_cols = set()
            for r in rows:
                row_key = r.get(idx, "")
                col_key = r.get(col, "")
                value = r.get(val, "0")
                try: value = float(value)
                except: continue
                all_cols.add(col_key)
                pivot.setdefault(row_key, {}).setdefault(col_key, []).append(value)
            all_cols = sorted(all_cols)
            lines = [f"{idx}\t" + "\t".join(all_cols)]
            for row_key in sorted(pivot.keys()):
                vals = []
                for c in all_cols:
                    v = pivot[row_key].get(c, [])
                    if not v: vals.append("")
                    elif aggfunc == "sum": vals.append(f"{sum(v):.4g}")
                    elif aggfunc == "avg": vals.append(f"{sum(v)/len(v):.4g}")
                    elif aggfunc == "count": vals.append(str(len(v)))
                lines.append(f"{row_key}\t" + "\t".join(vals))
            return "\n".join(lines)

        elif name == "sheet_columns":
            headers, rows = _read_csv(args["path"], limit=10)
            types = {}
            for h in headers:
                vals = [r.get(h, "") for r in rows]
                if all(_is_num(v) for v in vals if v):
                    types[h] = "number"
                elif all(v.lower() in ("true", "false", "yes", "no") for v in vals if v):
                    types[h] = "boolean"
                else:
                    types[h] = "text"
            return "\n".join(f"{h}: {t}" for h, t in zip(headers, types.values()))

        elif name == "sheet_row_count":
            count = 0
            with open(args["path"], newline="", encoding="utf-8", errors="replace") as f:
                count = sum(1 for _ in f) - 1  # minus header
            return f"Rows: {count}"

        elif name == "sheet_find":
            search = args["search"]
            case = args.get("case_sensitive", False)
            headers, rows = _read_csv(args["path"], limit=100000)
            matches = []
            for i, r in enumerate(rows, 1):
                for h in headers:
                    cell = str(r.get(h, ""))
                    if case:
                        if search in cell:
                            matches.append(f"Row {i}, {h}: {cell}")
                    else:
                        if search.lower() in cell.lower():
                            matches.append(f"Row {i}, {h}: {cell}")
            return "\n".join(matches[:50]) or "(no matches)"

        elif name == "sheet_add_column":
            headers, rows = _read_csv(args["path"], limit=100000)
            new_col = args["name"]
            formula = args.get("formula", "")
            default = args.get("default", "")
            headers.append(new_col)
            for r in rows:
                if formula:
                    try:
                        r[new_col] = str(eval(formula, {"row": r, "__builtins__": {}}))
                    except:
                        r[new_col] = default
                else:
                    r[new_col] = default
            output = args["output"]
            with open(output, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                w.writerows(rows)
            return f"Added column '{new_col}', saved to {output}"

        elif name == "sheet_merge":
            h1, r1 = _read_csv(args["left"], limit=100000)
            h2, r2 = _read_csv(args["right"], limit=100000)
            on = args["on"]
            how = args.get("how", "inner")
            r2_map = {}
            for r in r2:
                key = r.get(on, "")
                r2_map.setdefault(key, []).append(r)
            merged = []
            matched_keys = set()
            for r in r1:
                key = r.get(on, "")
                if key in r2_map:
                    matched_keys.add(key)
                    for r2_row in r2_map[key]:
                        merged.append({**r, **r2_row})
                elif how in ("left", "outer"):
                    merged.append(r)
            if how in ("right", "outer"):
                for r in r2:
                    key = r.get(on, "")
                    if key not in matched_keys:
                        merged.append(r)
            all_headers = list(dict.fromkeys(h1 + h2))
            output = args["output"]
            with open(output, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=all_headers, extrasaction="ignore")
                w.writeheader()
                w.writerows(merged)
            return f"Merged {len(merged)} rows ({how} join), saved to {output}"

        elif name == "sheet_dedup":
            headers, rows = _read_csv(args["path"], limit=100000)
            col = args.get("column")
            seen = set()
            unique = []
            for r in rows:
                key = r.get(col, "") if col else tuple(r.values())
                if key not in seen:
                    seen.add(key)
                    unique.append(r)
            output = args["output"]
            with open(output, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
                w.writerows(unique)
            removed = len(rows) - len(unique)
            return f"Removed {removed} duplicates, {len(unique)} unique rows saved to {output}"

        elif name == "sheet_sample":
            import random
            headers, rows = _read_csv(args["path"], limit=100000)
            count = args.get("count", 10)
            if args.get("seed"):
                random.seed(args["seed"])
            sample = random.sample(rows, min(count, len(rows)))
            lines = ["\t".join(headers)]
            for r in sample:
                lines.append("\t".join(str(r.get(h, "")) for h in headers))
            return "\n".join(lines)

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"


def _is_num(v):
    try:
        float(v)
        return True
    except:
        return False
