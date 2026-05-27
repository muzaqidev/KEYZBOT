"""Math, statistics, and calculation tools."""

import math, statistics, re

TOOL_DEFS = [
    {"type": "function", "function": {"name": "calculate", "description": "Evaluate a math expression. Supports +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e.", "parameters": {"type": "object", "properties": {"expression": {"type": "string", "description": "Math expression (e.g. '2**10', 'sqrt(144)', 'sin(pi/2)')"}}, "required": ["expression"]}}},
    {"type": "function", "function": {"name": "unit_convert", "description": "Convert between units: length, weight, temperature, volume, speed, data, time.", "parameters": {"type": "object", "properties": {"value": {"type": "number", "description": "Value to convert"}, "from": {"type": "string", "description": "Source unit (e.g. 'km', 'lb', 'celsius', 'gb')"}, "to": {"type": "string", "description": "Target unit (e.g. 'miles', 'kg', 'fahrenheit', 'mb')"}}, "required": ["value", "from", "to"]}}},
    {"type": "function", "function": {"name": "statistics_calc", "description": "Calculate statistics for a list of numbers: mean, median, mode, stdev, variance, min, max, sum.", "parameters": {"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "number"}, "description": "List of numbers"}}, "required": ["numbers"]}}},
    {"type": "function", "function": {"name": "number_base_convert", "description": "Convert numbers between bases: binary, octal, decimal, hex.", "parameters": {"type": "object", "properties": {"number": {"type": "string", "description": "Number to convert"}, "from_base": {"type": "integer", "description": "Source base (2, 8, 10, 16)"}, "to_base": {"type": "integer", "description": "Target base (2, 8, 10, 16)"}}, "required": ["number", "from_base", "to_base"]}}},
    {"type": "function", "function": {"name": "matrix_ops", "description": "Matrix operations: add, subtract, multiply, transpose, determinant.", "parameters": {"type": "object", "properties": {"operation": {"type": "string", "enum": ["add", "subtract", "multiply", "transpose", "determinant"], "description": "Operation"}, "matrix_a": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}, "description": "First matrix (2D array)"}, "matrix_b": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}, "description": "Second matrix (for add/subtract/multiply)"}}, "required": ["operation", "matrix_a"]}}},
    {"type": "function", "function": {"name": "equation_solve", "description": "Solve simple algebraic equations (linear, quadratic).", "parameters": {"type": "object", "properties": {"equation": {"type": "string", "description": "Equation (e.g. '2x + 5 = 15', 'x^2 - 4x + 4 = 0')"}}, "required": ["equation"]}}},
    {"type": "function", "function": {"name": "percentage_calc", "description": "Calculate percentages: X% of Y, X is what % of Y, % change from X to Y.", "parameters": {"type": "object", "properties": {"type": {"type": "string", "enum": ["percent_of", "is_what_percent", "percent_change"], "description": "Calculation type"}, "value1": {"type": "number", "description": "First value"}, "value2": {"type": "number", "description": "Second value"}}, "required": ["type", "value1", "value2"]}}},
    {"type": "function", "function": {"name": "random_generate", "description": "Generate random numbers, strings, or choices.", "parameters": {"type": "object", "properties": {"type": {"type": "string", "enum": ["int", "float", "string", "choice", "uuid"], "description": "Random type"}, "min": {"type": "number", "description": "Min value for int/float"}, "max": {"type": "number", "description": "Max value for int/float"}, "length": {"type": "integer", "description": "Length for string"}, "choices": {"type": "array", "description": "List to choose from"}, "count": {"type": "integer", "description": "How many to generate (default 1)"}}, "required": ["type"]}}},
    {"type": "function", "function": {"name": "fibonacci", "description": "Generate Fibonacci sequence up to N numbers.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many numbers (default 10)"}}, "required": []}}},
    {"type": "function", "function": {"name": "prime_check", "description": "Check if a number is prime, and find prime factors.", "parameters": {"type": "object", "properties": {"number": {"type": "integer", "description": "Number to check"}}, "required": ["number"]}}},
    {"type": "function", "function": {"name": "factorial", "description": "Calculate factorial of a number.", "parameters": {"type": "object", "properties": {"number": {"type": "integer", "description": "Non-negative integer"}}, "required": ["number"]}}},
    {"type": "function", "function": {"name": "geometry_calc", "description": "Calculate geometry formulas: area, perimeter, volume for various shapes.", "parameters": {"type": "object", "properties": {"shape": {"type": "string", "enum": ["circle", "rectangle", "triangle", "sphere", "cylinder", "cone", "cube"], "description": "Shape type"}, "measurements": {"type": "object", "description": "Shape measurements as JSON (e.g. {\"radius\": 5})"}}, "required": ["shape", "measurements"]}}},
    {"type": "function", "function": {"name": "interest_calc", "description": "Calculate simple or compound interest.", "parameters": {"type": "object", "properties": {"principal": {"type": "number", "description": "Principal amount"}, "rate": {"type": "number", "description": "Annual interest rate (%)"}, "time": {"type": "number", "description": "Time in years"}, "type": {"type": "string", "enum": ["simple", "compound"], "description": "Interest type (default compound)"}, "compounds_per_year": {"type": "integer", "description": "Compounding frequency per year (default 12)"}}, "required": ["principal", "rate", "time"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "calculate":
            safe_ns = {"__builtins__": {}, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan, "log": math.log, "log10": math.log10, "log2": math.log2, "abs": abs, "round": round, "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor, "pow": pow, "exp": math.exp, "factorial": math.factorial}
            result = eval(args["expression"], safe_ns)
            return f"{args['expression']} = {result}"

        elif name == "unit_convert":
            val = args["value"]
            fr = args["from"].lower()
            to = args["to"].lower()
            conversions = {
                ("km", "miles"): 0.621371, ("miles", "km"): 1.60934,
                ("m", "feet"): 3.28084, ("feet", "m"): 0.3048,
                ("m", "inches"): 39.3701, ("inches", "m"): 0.0254,
                ("cm", "inches"): 0.393701, ("inches", "cm"): 2.54,
                ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
                ("kg", "oz"): 35.274, ("oz", "kg"): 0.0283495,
                ("g", "oz"): 0.035274, ("oz", "g"): 28.3495,
                ("liters", "gallons"): 0.264172, ("gallons", "liters"): 3.78541,
                ("ml", "fl_oz"): 0.033814, ("fl_oz", "ml"): 29.5735,
                ("km/h", "mph"): 0.621371, ("mph", "km/h"): 1.60934,
                ("m/s", "km/h"): 3.6, ("km/h", "m/s"): 0.277778,
                ("gb", "mb"): 1024, ("mb", "gb"): 1/1024,
                ("mb", "kb"): 1024, ("kb", "mb"): 1/1024,
                ("gb", "kb"): 1024*1024, ("kb", "gb"): 1/(1024*1024),
                ("hours", "minutes"): 60, ("minutes", "hours"): 1/60,
                ("days", "hours"): 24, ("hours", "days"): 1/24,
                ("weeks", "days"): 7, ("days", "weeks"): 1/7,
            }
            if fr == "celsius" and to == "fahrenheit":
                return f"{val}°C = {val * 9/5 + 32:.2f}°F"
            elif fr == "fahrenheit" and to == "celsius":
                return f"{val}°F = {(val - 32) * 5/9:.2f}°C"
            elif fr == "celsius" and to == "kelvin":
                return f"{val}°C = {val + 273.15:.2f}K"
            elif fr == "kelvin" and to == "celsius":
                return f"{val}K = {val - 273.15:.2f}°C"
            factor = conversions.get((fr, to))
            if factor:
                return f"{val} {fr} = {val * factor:.6g} {to}"
            return f"Unknown conversion: {fr} -> {to}"

        elif name == "statistics_calc":
            nums = args["numbers"]
            return "\n".join([
                f"Count: {len(nums)}",
                f"Sum: {sum(nums):.6g}",
                f"Mean: {statistics.mean(nums):.6g}",
                f"Median: {statistics.median(nums):.6g}",
                f"Stdev: {statistics.stdev(nums):.6g}" if len(nums) > 1 else "Stdev: N/A",
                f"Variance: {statistics.variance(nums):.6g}" if len(nums) > 1 else "Variance: N/A",
                f"Min: {min(nums):.6g}",
                f"Max: {max(nums):.6g}",
            ])

        elif name == "number_base_convert":
            num = args["number"]
            fr = args["from_base"]
            to = args["to_base"]
            decimal = int(num, fr)
            if to == 2: return f"{num} (base {fr}) = {bin(decimal)} (base 2)"
            elif to == 8: return f"{num} (base {fr}) = {oct(decimal)} (base 8)"
            elif to == 10: return f"{num} (base {fr}) = {decimal} (base 10)"
            elif to == 16: return f"{num} (base {fr}) = {hex(decimal)} (base 16)"
            return f"Unsupported target base: {to}"

        elif name == "matrix_ops":
            import numpy as np
            op = args["operation"]
            a = np.array(args["matrix_a"])
            if op == "transpose":
                return str(a.T.tolist())
            elif op == "determinant":
                return f"Determinant: {np.linalg.det(a):.6g}"
            b = np.array(args["matrix_b"])
            if op == "add": return str((a + b).tolist())
            elif op == "subtract": return str((a - b).tolist())
            elif op == "multiply": return str(np.matmul(a, b).tolist())
            return f"Unknown operation: {op}"

        elif name == "equation_solve":
            eq = args["equation"]
            # Linear: ax + b = c
            m = re.match(r'([-\d.]*)\s*x\s*([+-]\s*[\d.]*)\s*=\s*([-\d.]*)', eq)
            if m:
                a = float(m.group(1) or 1)
                b = float(m.group(2).replace(" ", "") or 0)
                c = float(m.group(3))
                x = (c - b) / a
                return f"x = {x:.6g}"
            # Quadratic: ax^2 + bx + c = 0
            m = re.match(r'([-\d.]*)\s*x\^2\s*([+-]\s*[\d.]*)\s*x\s*([+-]\s*[\d.]*)\s*=\s*0', eq)
            if m:
                a = float(m.group(1) or 1)
                b = float(m.group(2).replace(" ", "") or 0)
                c = float(m.group(3).replace(" ", "") or 0)
                disc = b**2 - 4*a*c
                if disc < 0:
                    return "No real solutions (discriminant < 0)"
                x1 = (-b + math.sqrt(disc)) / (2*a)
                x2 = (-b - math.sqrt(disc)) / (2*a)
                return f"x1 = {x1:.6g}\nx2 = {x2:.6g}"
            return "Could not parse equation. Format: '2x + 5 = 15' or 'x^2 - 4x + 4 = 0'"

        elif name == "percentage_calc":
            t = args["type"]
            v1, v2 = args["value1"], args["value2"]
            if t == "percent_of":
                return f"{v1}% of {v2} = {v1 * v2 / 100:.6g}"
            elif t == "is_what_percent":
                return f"{v1} is {v1 / v2 * 100:.4g}% of {v2}"
            elif t == "percent_change":
                change = (v2 - v1) / v1 * 100
                return f"Change from {v1} to {v2}: {change:+.4g}%"

        elif name == "random_generate":
            import random, string, uuid as uuid_mod
            t = args["type"]
            count = args.get("count", 1)
            if t == "int":
                nums = [random.randint(int(args.get("min", 0)), int(args.get("max", 100))) for _ in range(count)]
                return "\n".join(str(n) for n in nums)
            elif t == "float":
                nums = [random.uniform(args.get("min", 0), args.get("max", 1)) for _ in range(count)]
                return "\n".join(f"{n:.6g}" for n in nums)
            elif t == "string":
                length = args.get("length", 16)
                chars = string.ascii_letters + string.digits
                return "\n".join("".join(random.choice(chars) for _ in range(length)) for _ in range(count))
            elif t == "choice":
                choices = args.get("choices", [])
                return "\n".join(str(random.choice(choices)) for _ in range(count))
            elif t == "uuid":
                return "\n".join(str(uuid_mod.uuid4()) for _ in range(count))
            return f"Unknown type: {t}"

        elif name == "fibonacci":
            count = args.get("count", 10)
            a, b = 0, 1
            seq = []
            for _ in range(count):
                seq.append(a)
                a, b = b, a + b
            return ", ".join(str(n) for n in seq)

        elif name == "prime_check":
            n = args["number"]
            if n < 2:
                return f"{n} is not prime"
            is_prime = True
            factors = []
            d = 2
            temp = n
            while d * d <= temp:
                while temp % d == 0:
                    factors.append(d)
                    temp //= d
                    is_prime = False
                d += 1
            if temp > 1:
                factors.append(temp)
            if is_prime:
                return f"{n} is prime"
            return f"{n} is not prime\nFactors: {' × '.join(str(f) for f in factors)} = {n}"

        elif name == "factorial":
            n = args["number"]
            if n < 0: return "Error: factorial not defined for negative numbers"
            if n > 20: return "Error: number too large (max 20)"
            return f"{n}! = {math.factorial(n)}"

        elif name == "geometry_calc":
            shape = args["shape"]
            m = args["measurements"]
            if shape == "circle":
                r = m["radius"]
                return f"Area: {math.pi * r**2:.4f}\nCircumference: {2 * math.pi * r:.4f}"
            elif shape == "rectangle":
                w, h = m["width"], m["height"]
                return f"Area: {w * h:.4f}\nPerimeter: {2 * (w + h):.4f}"
            elif shape == "triangle":
                a, b, c = m["a"], m["b"], m["c"]
                s = (a + b + c) / 2
                area = math.sqrt(s * (s-a) * (s-b) * (s-c))
                return f"Area: {area:.4f}\nPerimeter: {a+b+c:.4f}"
            elif shape == "sphere":
                r = m["radius"]
                return f"Volume: {4/3 * math.pi * r**3:.4f}\nSurface Area: {4 * math.pi * r**2:.4f}"
            elif shape == "cylinder":
                r, h = m["radius"], m["height"]
                return f"Volume: {math.pi * r**2 * h:.4f}\nSurface Area: {2 * math.pi * r * (r + h):.4f}"
            elif shape == "cone":
                r, h = m["radius"], m["height"]
                s = math.sqrt(r**2 + h**2)
                return f"Volume: {1/3 * math.pi * r**2 * h:.4f}\nSurface Area: {math.pi * r * (r + s):.4f}"
            elif shape == "cube":
                s = m["side"]
                return f"Volume: {s**3:.4f}\nSurface Area: {6 * s**2:.4f}"
            return f"Unknown shape: {shape}"

        elif name == "interest_calc":
            p = args["principal"]
            r = args["rate"] / 100
            t = args["time"]
            itype = args.get("type", "compound")
            n = args.get("compounds_per_year", 12)
            if itype == "simple":
                interest = p * r * t
                total = p + interest
                return f"Simple Interest: {interest:.2f}\nTotal Amount: {total:.2f}"
            else:
                total = p * (1 + r/n) ** (n*t)
                interest = total - p
                return f"Compound Interest: {interest:.2f}\nTotal Amount: {total:.2f}"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
