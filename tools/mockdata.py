"""Mock data generation tools — names, addresses, lorem ipsum, test data."""

import random, string, json, os, hashlib, time

TOOL_DEFS = [
    {"type": "function", "function": {"name": "generate_names", "description": "Generate random realistic names.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "Number of names (default 10)"}, "format": {"type": "string", "enum": ["full", "first", "last", "username"], "description": "Name format (default full)"}, "gender": {"type": "string", "enum": ["male", "female", "any"], "description": "Gender (default any)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_emails", "description": "Generate random email addresses.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "Number of emails (default 10)"}, "domain": {"type": "string", "description": "Email domain (default random)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_phones", "description": "Generate random phone numbers.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "Number of phones (default 10)"}, "country": {"type": "string", "enum": ["US", "UK", "ID", "JP", "DE"], "description": "Country format (default US)"}, "format": {"type": "string", "enum": ["national", "international", "digits"], "description": "Phone format (default national)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_addresses", "description": "Generate random addresses.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "Number of addresses (default 5)"}, "country": {"type": "string", "enum": ["US", "UK", "ID"], "description": "Country (default US)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_lorem", "description": "Generate Lorem Ipsum placeholder text.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "Number of paragraphs/sentences/words (default 3)"}, "unit": {"type": "string", "enum": ["paragraphs", "sentences", "words"], "description": "Unit (default paragraphs)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_numbers", "description": "Generate random numbers within a range.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 10)"}, "min": {"type": "number", "description": "Minimum value (default 0)"}, "max": {"type": "number", "description": "Maximum value (default 100)"}, "decimal": {"type": "boolean", "description": "Allow decimals (default false)"}, "unique": {"type": "boolean", "description": "No duplicates (default false)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_dates", "description": "Generate random dates.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 10)"}, "start": {"type": "string", "description": "Start date YYYY-MM-DD (default 2020-01-01)"}, "end": {"type": "string", "description": "End date YYYY-MM-DD (default 2026-12-31)"}, "format": {"type": "string", "description": "Output format (default YYYY-MM-DD)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_users", "description": "Generate complete fake user profiles with name, email, phone, address.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "Number of users (default 5)"}, "format": {"type": "string", "enum": ["json", "csv", "table"], "description": "Output format (default json)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_passwords", "description": "Generate random secure passwords.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 5)"}, "length": {"type": "integer", "description": "Password length (default 16)"}, "memorable": {"type": "boolean", "description": "Make memorable (word-based, default false)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_json", "description": "Generate structured JSON data from a template schema.", "parameters": {"type": "object", "properties": {"schema": {"type": "string", "description": "JSON template with type hints (e.g. '{\"name\": \"name\", \"age\": \"int:18-65\", \"email\": \"email\"}')"}, "count": {"type": "integer", "description": "Number of records (default 5)"}}, "required": ["schema"]}}},
    {"type": "function", "function": {"name": "generate_csv", "description": "Generate a CSV file with mock data.", "parameters": {"type": "object", "properties": {"output": {"type": "string", "description": "Output CSV path"}, "columns": {"type": "string", "description": "Column definitions (e.g. 'name,email,age:int:18-65,active:bool')"}, "count": {"type": "integer", "description": "Number of rows (default 100)"}}, "required": ["output", "columns"]}}},
    {"type": "function", "function": {"name": "generate_uuids", "description": "Generate UUID v4 identifiers.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 10)"}, "format": {"type": "string", "enum": ["standard", "no-dash", "upper"], "description": "Format (default standard)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_ips", "description": "Generate random IP addresses.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 10)"}, "version": {"type": "integer", "enum": [4, 6], "description": "IP version (default 4)"}, "private": {"type": "boolean", "description": "Only private ranges (default false)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_urls", "description": "Generate random URLs.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 10)"}, "tld": {"type": "string", "description": "Top-level domain (default random)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_colors", "description": "Generate random colors in HEX, RGB, or HSL.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 10)"}, "format": {"type": "string", "enum": ["hex", "rgb", "hsl"], "description": "Color format (default hex)"}, "palette": {"type": "boolean", "description": "Generate harmonious palette (default false)"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_words", "description": "Generate random words from a wordlist.", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "How many (default 10)"}, "min_length": {"type": "integer", "description": "Min word length (default 3)"}, "max_length": {"type": "integer", "description": "Max word length (default 10)"}}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]

_FIRST_NAMES_M = ["James", "John", "Robert", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin"]
_FIRST_NAMES_F = ["Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily", "Donna"]
_LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
_STREETS = ["Main St", "Oak Ave", "Elm St", "Park Blvd", "Maple Dr", "Cedar Ln", "Pine St", "Washington Ave", "Lake Dr", "Hill Rd"]
_CITIES = ["Springfield", "Franklin", "Greenville", "Bristol", "Clinton", "Kingston", "Madison", "Oxford", "Riverside", "Fairview"]
_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com", "icloud.com", "mail.com", "zoho.com"]
_TLDS = [".com", ".org", ".net", ".io", ".dev", ".co", ".app", ".tech"]
_WORDS = ["apple", "brave", "cloud", "delta", "eagle", "flame", "grace", "honor", "ivory", "jewel", "karma", "light", "magic", "noble", "ocean", "pearl", "quest", "royal", "storm", "tiger", "ultra", "vivid", "wonder", "xenon", "yield", "zenith", "amber", "blaze", "coral", "drift", "ember", "frost", "glyph", "hover", "iris", "jade", "knot", "lunar", "mocha", "nexus"]


def execute(name, args, work_dir=None):
    try:
        if name == "generate_names":
            count = args.get("count", 10)
            fmt = args.get("format", "full")
            gender = args.get("gender", "any")
            names = []
            for _ in range(count):
                if gender == "male": fn = random.choice(_FIRST_NAMES_M)
                elif gender == "female": fn = random.choice(_FIRST_NAMES_F)
                else: fn = random.choice(_FIRST_NAMES_M + _FIRST_NAMES_F)
                ln = random.choice(_LAST_NAMES)
                if fmt == "first": names.append(fn)
                elif fmt == "last": names.append(ln)
                elif fmt == "username": names.append(f"{fn.lower()}{random.randint(1,999)}")
                else: names.append(f"{fn} {ln}")
            return "\n".join(names)

        elif name == "generate_emails":
            count = args.get("count", 10)
            domain = args.get("domain", "")
            emails = []
            for _ in range(count):
                fn = random.choice(_FIRST_NAMES_M + _FIRST_NAMES_F).lower()
                ln = random.choice(_LAST_NAMES).lower()
                d = domain or random.choice(_DOMAINS)
                sep = random.choice([".", "_", ""])
                num = random.randint(0, 99)
                emails.append(f"{fn}{sep}{ln}{num}@{d}")
            return "\n".join(emails)

        elif name == "generate_phones":
            count = args.get("count", 10)
            country = args.get("country", "US")
            phones = []
            for _ in range(count):
                if country == "US":
                    p = f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"
                elif country == "UK":
                    p = f"+44 {random.randint(7000,7999)} {random.randint(100000,999999)}"
                elif country == "ID":
                    p = f"+62 {random.randint(810,899)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
                elif country == "JP":
                    p = f"+81 {random.randint(90,99)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
                elif country == "DE":
                    p = f"+49 {random.randint(150,170)} {random.randint(1000000,9999999)}"
                else:
                    p = f"+{random.randint(1,99)} {random.randint(100,999)} {random.randint(1000000,9999999)}"
                phones.append(p)
            return "\n".join(phones)

        elif name == "generate_addresses":
            count = args.get("count", 5)
            addresses = []
            for _ in range(count):
                num = random.randint(1, 9999)
                street = random.choice(_STREETS)
                city = random.choice(_CITIES)
                state = random.choice(["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"])
                zip_code = random.randint(10000, 99999)
                addresses.append(f"{num} {street}, {city}, {state} {zip_code}")
            return "\n".join(addresses)

        elif name == "generate_lorem":
            count = args.get("count", 3)
            unit = args.get("unit", "paragraphs")
            lorem = "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua"
            words = lorem.split()
            if unit == "words":
                return " ".join(random.choices(words, k=count))
            elif unit == "sentences":
                sentences = []
                for _ in range(count):
                    s = " ".join(random.choices(words, k=random.randint(8, 20)))
                    sentences.append(s.capitalize() + ".")
                return " ".join(sentences)
            else:
                paragraphs = []
                for _ in range(count):
                    sents = []
                    for _ in range(random.randint(3, 6)):
                        s = " ".join(random.choices(words, k=random.randint(8, 20)))
                        sents.append(s.capitalize() + ".")
                    paragraphs.append(" ".join(sents))
                return "\n\n".join(paragraphs)

        elif name == "generate_numbers":
            count = args.get("count", 10)
            min_val = args.get("min", 0)
            max_val = args.get("max", 100)
            decimal = args.get("decimal", False)
            unique = args.get("unique", False)
            if unique:
                if decimal:
                    nums = set()
                    while len(nums) < count:
                        nums.add(round(random.uniform(min_val, max_val), 2))
                    return "\n".join(str(n) for n in nums)
                else:
                    return "\n".join(str(n) for n in random.sample(range(int(min_val), int(max_val) + 1), min(count, int(max_val) - int(min_val) + 1)))
            if decimal:
                return "\n".join(str(round(random.uniform(min_val, max_val), 2)) for _ in range(count))
            return "\n".join(str(random.randint(int(min_val), int(max_val))) for _ in range(count))

        elif name == "generate_dates":
            count = args.get("count", 10)
            start = args.get("start", "2020-01-01")
            end = args.get("end", "2026-12-31")
            fmt = args.get("format", "%Y-%m-%d")
            from datetime import datetime, timedelta
            s = datetime.strptime(start, "%Y-%m-%d")
            e = datetime.strptime(end, "%Y-%m-%d")
            delta = (e - s).days
            dates = []
            for _ in range(count):
                d = s + timedelta(days=random.randint(0, delta))
                dates.append(d.strftime(fmt))
            return "\n".join(dates)

        elif name == "generate_users":
            count = args.get("count", 5)
            fmt = args.get("format", "json")
            users = []
            for _ in range(count):
                fn = random.choice(_FIRST_NAMES_M + _FIRST_NAMES_F)
                ln = random.choice(_LAST_NAMES)
                users.append({
                    "name": f"{fn} {ln}",
                    "username": f"{fn.lower()}{random.randint(1,999)}",
                    "email": f"{fn.lower()}.{ln.lower()}{random.randint(1,99)}@{random.choice(_DOMAINS)}",
                    "phone": f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}",
                    "address": f"{random.randint(1,9999)} {random.choice(_STREETS)}, {random.choice(_CITIES)}",
                    "age": random.randint(18, 75),
                    "company": f"{random.choice(_WORDS).title()} Corp",
                })
            if fmt == "json":
                return json.dumps(users, indent=2)
            elif fmt == "csv":
                lines = [",".join(users[0].keys())]
                for u in users:
                    lines.append(",".join(str(v) for v in u.values()))
                return "\n".join(lines)
            else:
                lines = []
                for u in users:
                    lines.append(" | ".join(f"{k}: {v}" for k, v in u.items()))
                    lines.append("---")
                return "\n".join(lines)

        elif name == "generate_passwords":
            count = args.get("count", 5)
            length = args.get("length", 16)
            memorable = args.get("memorable", False)
            passwords = []
            for _ in range(count):
                if memorable:
                    words = random.sample(_WORDS, 4)
                    sep = random.choice(["-", ".", "_", ""])
                    pw = sep.join(w.capitalize() for w in words) + str(random.randint(10, 99))
                else:
                    chars = string.ascii_letters + string.digits + "!@#$%^&*"
                    pw = "".join(random.choice(chars) for _ in range(length))
                passwords.append(pw)
            return "\n".join(passwords)

        elif name == "generate_json":
            schema = json.loads(args["schema"])
            count = args.get("count", 5)
            records = []
            for _ in range(count):
                record = {}
                for key, type_hint in schema.items():
                    if type_hint == "name": record[key] = f"{random.choice(_FIRST_NAMES_M + _FIRST_NAMES_F)} {random.choice(_LAST_NAMES)}"
                    elif type_hint == "email": record[key] = f"{random.choice(_WORDS)}{random.randint(1,99)}@{random.choice(_DOMAINS)}"
                    elif type_hint == "phone": record[key] = f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"
                    elif type_hint.startswith("int"):
                        parts = type_hint.split(":")
                        if len(parts) > 1 and "-" in parts[1]:
                            lo, hi = parts[1].split("-")
                            record[key] = random.randint(int(lo), int(hi))
                        else:
                            record[key] = random.randint(0, 100)
                    elif type_hint.startswith("float"):
                        record[key] = round(random.uniform(0, 100), 2)
                    elif type_hint == "bool": record[key] = random.choice([True, False])
                    elif type_hint == "uuid": record[key] = str(__import__("uuid").uuid4())
                    elif type_hint == "date": record[key] = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                    elif type_hint == "url": record[key] = f"https://{random.choice(_WORDS)}.com"
                    elif type_hint == "ip": record[key] = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
                    else: record[key] = f"{random.choice(_WORDS)}_{random.randint(1,999)}"
                records.append(record)
            return json.dumps(records, indent=2)

        elif name == "generate_csv":
            output = args["output"]
            col_defs = args["columns"].split(",")
            count = args.get("count", 100)
            headers = []
            generators = []
            for col_def in col_defs:
                parts = col_def.strip().split(":")
                name = parts[0]
                headers.append(name)
                if len(parts) == 1 or parts[1] == "str":
                    generators.append(lambda: random.choice(_WORDS))
                elif parts[1] == "int":
                    lo, hi = (int(x) for x in parts[2].split("-")) if len(parts) > 2 else (0, 100)
                    generators.append(lambda lo=lo, hi=hi: random.randint(lo, hi))
                elif parts[1] == "float":
                    generators.append(lambda: round(random.uniform(0, 100), 2))
                elif parts[1] == "bool":
                    generators.append(lambda: random.choice(["true", "false"]))
                elif parts[1] == "email":
                    generators.append(lambda: f"{random.choice(_WORDS)}{random.randint(1,99)}@{random.choice(_DOMAINS)}")
                elif parts[1] == "name":
                    generators.append(lambda: f"{random.choice(_FIRST_NAMES_M + _FIRST_NAMES_F)} {random.choice(_LAST_NAMES)}")
                elif parts[1] == "date":
                    generators.append(lambda: f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}")
                else:
                    generators.append(lambda: random.choice(_WORDS))
            with open(output, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(headers)
                for _ in range(count):
                    w.writerow([g() for g in generators])
            return f"Generated {count} rows with {len(headers)} columns to {output}"

        elif name == "generate_uuids":
            import uuid
            count = args.get("count", 10)
            fmt = args.get("format", "standard")
            uuids = []
            for _ in range(count):
                u = str(uuid.uuid4())
                if fmt == "no-dash": u = u.replace("-", "")
                elif fmt == "upper": u = u.upper()
                uuids.append(u)
            return "\n".join(uuids)

        elif name == "generate_ips":
            count = args.get("count", 10)
            version = args.get("version", 4)
            private = args.get("private", False)
            ips = []
            for _ in range(count):
                if version == 4:
                    if private:
                        prefix = random.choice(["10.", "172.16.", "192.168."])
                        if prefix == "10.":
                            ips.append(f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}")
                        elif prefix == "172.16.":
                            ips.append(f"172.{random.randint(16,31)}.{random.randint(0,255)}.{random.randint(1,254)}")
                        else:
                            ips.append(f"192.168.{random.randint(0,255)}.{random.randint(1,254)}")
                    else:
                        ips.append(f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}")
                else:
                    segments = [format(random.randint(0, 65535), 'x') for _ in range(8)]
                    ips.append(":".join(segments))
            return "\n".join(ips)

        elif name == "generate_urls":
            count = args.get("count", 10)
            tld = args.get("tld", "")
            urls = []
            for _ in range(count):
                word = random.choice(_WORDS)
                t = tld or random.choice(_TLDS)
                path = random.choice(["", f"/{random.choice(_WORDS)}", f"/{random.choice(_WORDS)}/{random.randint(1,999)}"])
                urls.append(f"https://{word}{t}{path}")
            return "\n".join(urls)

        elif name == "generate_colors":
            count = args.get("count", 10)
            fmt = args.get("format", "hex")
            colors = []
            for _ in range(count):
                r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
                if fmt == "hex":
                    colors.append(f"#{r:02x}{g:02x}{b:02x}")
                elif fmt == "rgb":
                    colors.append(f"rgb({r}, {g}, {b})")
                elif fmt == "hsl":
                    h = random.randint(0, 360)
                    s = random.randint(20, 100)
                    l = random.randint(20, 80)
                    colors.append(f"hsl({h}, {s}%, {l}%)")
            return "\n".join(colors)

        elif name == "generate_words":
            count = args.get("count", 10)
            min_len = args.get("min_length", 3)
            max_len = args.get("max_length", 10)
            filtered = [w for w in _WORDS if min_len <= len(w) <= max_len]
            return "\n".join(random.choices(filtered, k=count))

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
