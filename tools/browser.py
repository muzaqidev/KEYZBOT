"""Headless browser automation tools — screenshot, scrape, fill forms, interact."""

import subprocess, os, json, time

TOOL_DEFS = [
    {"type": "function", "function": {"name": "browser_screenshot", "description": "Take a screenshot of a webpage using headless browser. Returns image path.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to screenshot"}, "output": {"type": "string", "description": "Output image path"}, "width": {"type": "integer", "description": "Viewport width (default 1280)"}, "height": {"type": "integer", "description": "Viewport height (default 720)"}, "full_page": {"type": "boolean", "description": "Capture full page scroll (default false)"}, "wait": {"type": "integer", "description": "Wait seconds after load (default 2)"}}, "required": ["url", "output"]}}},
    {"type": "function", "function": {"name": "browser_pdf", "description": "Generate a PDF from a webpage using headless browser.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to convert"}, "output": {"type": "string", "description": "Output PDF path"}, "format": {"type": "string", "enum": ["A4", "Letter", "Legal"], "description": "Page format (default A4)"}, "landscape": {"type": "boolean", "description": "Landscape orientation (default false)"}}, "required": ["url", "output"]}}},
    {"type": "function", "function": {"name": "browser_extract", "description": "Extract text content from a webpage, removing scripts and styles.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to extract from"}, "selector": {"type": "string", "description": "CSS selector to extract specific element"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_links", "description": "Extract all links from a webpage.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to scan"}, "filter": {"type": "string", "description": "Filter links containing this text"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_images", "description": "Extract all image URLs from a webpage.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to scan"}, "download": {"type": "boolean", "description": "Download images to local dir (default false)"}, "output_dir": {"type": "string", "description": "Directory to save downloaded images"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_meta", "description": "Extract meta tags, Open Graph, and Twitter Card data from a URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to analyze"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_status", "description": "Check HTTP status code, response time, and redirect chain of a URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to check"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_headers", "description": "Get HTTP response headers from a URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to check"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_cookies", "description": "Get cookies from a URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to check"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_performance", "description": "Measure page load performance: DNS, connect, TTFB, download, total time.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to test"}, "runs": {"type": "integer", "description": "Number of test runs (default 3)"}}, "required": ["url"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        import requests

        if name == "browser_screenshot":
            url = args["url"]
            output = args["output"]
            width = args.get("width", 1280)
            height = args.get("height", 720)
            full_page = args.get("full_page", False)
            wait = args.get("wait", 2)

            # Try playwright first
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": width, "height": height})
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    if wait:
                        time.sleep(wait)
                    page.screenshot(path=output, full_page=full_page)
                    browser.close()
                return f"Screenshot saved to {output} ({os.path.getsize(output)//1024}KB)"
            except ImportError:
                pass

            # Try puppeteer via node
            js = f"""
            const puppeteer = require('puppeteer');
            (async () => {{
                const browser = await puppeteer.launch({{headless: true}});
                const page = await browser.newPage();
                await page.setViewport({{width: {width}, height: {height}}});
                await page.goto('{url}', {{waitUntil: 'networkidle0', timeout: 30000}});
                await new Promise(r => setTimeout(r, {wait * 1000}));
                await page.screenshot({{path: '{output}', fullPage: {'true' if full_page else 'false'}}});
                await browser.close();
            }})();
            """
            r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=45)
            if r.returncode == 0 and os.path.exists(output):
                return f"Screenshot saved to {output} ({os.path.getsize(output)//1024}KB)"

            # Fallback: use requests + html2canvas approach
            resp = requests.get(url, timeout=15)
            with open(output.replace('.png', '.html'), 'w') as f:
                f.write(resp.text)
            return "Playwright/Puppeteer not available. Saved HTML instead."

        elif name == "browser_pdf":
            url = args["url"]
            output = args["output"]
            fmt = args.get("format", "A4")
            landscape = args.get("landscape", False)
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.pdf(path=output, format=fmt, landscape=landscape)
                    browser.close()
                return f"PDF saved to {output} ({os.path.getsize(output)//1024}KB)"
            except ImportError:
                return "Error: playwright not installed. Run: pip install playwright && playwright install chromium"

        elif name == "browser_extract":
            url = args["url"]
            selector = args.get("selector", "")
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            text = resp.text
            if selector:
                # Simple CSS selector extraction
                import re
                tag = selector.strip('.#')
                if selector.startswith('.'):
                    pattern = rf'class="[^"]*{tag}[^"]*"[^>]*>(.*?)</'
                elif selector.startswith('#'):
                    pattern = rf'id="{tag}"[^>]*>(.*?)</'
                else:
                    pattern = rf'<{tag}[^>]*>(.*?)</{tag}>'
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                text = "\n".join(matches)
            else:
                # Strip HTML tags for clean text
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
            return text[:8000] if text else "(empty)"

        elif name == "browser_links":
            import re
            resp = requests.get(args["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            links = re.findall(r'href=["\']([^"\']+)["\']', resp.text)
            filt = args.get("filter", "")
            if filt:
                links = [l for l in links if filt.lower() in l.lower()]
            unique = list(dict.fromkeys(links))
            return "\n".join(unique[:100]) or "(no links found)"

        elif name == "browser_images":
            import re
            resp = requests.get(args["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', resp.text)
            images += re.findall(r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)', resp.text)
            unique = list(dict.fromkeys(images))
            if args.get("download") and args.get("output_dir"):
                os.makedirs(args["output_dir"], exist_ok=True)
                for img_url in unique[:20]:
                    try:
                        if not img_url.startswith("http"):
                            from urllib.parse import urljoin
                            img_url = urljoin(args["url"], img_url)
                        r = requests.get(img_url, timeout=10)
                        fname = os.path.basename(img_url).split("?")[0]
                        with open(os.path.join(args["output_dir"], fname), 'wb') as f:
                            f.write(r.content)
                    except:
                        continue
            return "\n".join(unique[:100]) or "(no images found)"

        elif name == "browser_meta":
            import re
            resp = requests.get(args["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text
            meta = {}
            # Title
            title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
            if title_match:
                meta["title"] = title_match.group(1)
            # Meta tags
            for m in re.finditer(r'<meta\s+([^>]+)>', html, re.IGNORECASE):
                attrs = m.group(1)
                name_match = re.search(r'name=["\']([^"\']+)["\']', attrs)
                prop_match = re.search(r'property=["\']([^"\']+)["\']', attrs)
                content_match = re.search(r'content=["\']([^"\']*)["\']', attrs)
                if (name_match or prop_match) and content_match:
                    key = (name_match or prop_match).group(1)
                    meta[key] = content_match.group(1)
            return json.dumps(meta, indent=2, ensure_ascii=False)

        elif name == "browser_status":
            url = args["url"]
            resp = requests.get(url, timeout=15, allow_redirects=True)
            history = []
            for r in resp.history:
                history.append(f"  {r.status_code} -> {r.url}")
            lines = [
                f"Final URL: {resp.url}",
                f"Status: {resp.status_code}",
                f"Redirects: {len(resp.history)}",
            ]
            if history:
                lines.append("Chain:")
                lines.extend(history)
            return "\n".join(lines)

        elif name == "browser_headers":
            resp = requests.head(args["url"], timeout=10, allow_redirects=True)
            lines = [f"{k}: {v}" for k, v in resp.headers.items()]
            return "\n".join(lines)

        elif name == "browser_cookies":
            session = requests.Session()
            session.get(args["url"], timeout=10)
            cookies = session.cookies.get_dict()
            return json.dumps(cookies, indent=2) if cookies else "(no cookies)"

        elif name == "browser_performance":
            url = args["url"]
            runs = args.get("runs", 3)
            results = []
            for i in range(runs):
                start = time.time()
                resp = requests.get(url, timeout=15)
                total = (time.time() - start) * 1000
                results.append({
                    "status": resp.status_code,
                    "total_ms": round(total),
                    "size_kb": len(resp.content) // 1024,
                })
            avg = sum(r["total_ms"] for r in results) / len(results)
            return f"Avg: {avg:.0f}ms over {runs} runs\n" + "\n".join(
                f"  Run {i+1}: {r['total_ms']}ms, {r['size_kb']}KB, HTTP {r['status']}"
                for i, r in enumerate(results)
            )

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
