"""Project auto-detect tool — detect project type from config files."""

import os, json

_DETECTIONS = [
    ("package.json", "node", "Node.js/JavaScript"),
    ("requirements.txt", "python", "Python"),
    ("setup.py", "python", "Python"),
    ("pyproject.toml", "python", "Python"),
    ("Cargo.toml", "rust", "Rust"),
    ("go.mod", "go", "Go"),
    ("pom.xml", "java", "Java (Maven)"),
    ("build.gradle", "java", "Java (Gradle)"),
    ("Gemfile", "ruby", "Ruby"),
    ("composer.json", "php", "PHP"),
    ("CMakeLists.txt", "cpp", "C/C++"),
    ("Makefile", "make", "Make"),
    ("Dockerfile", "docker", "Docker"),
    ("docker-compose.yml", "docker", "Docker Compose"),
    ("tsconfig.json", "typescript", "TypeScript"),
    (".github/workflows", "github-actions", "GitHub Actions"),
    ("pubspec.yaml", "dart", "Dart/Flutter"),
    ("build.sbt", "scala", "Scala"),
    ("mix.exs", "elixir", "Elixir"),
]

_TEST_FRAMEWORKS = [
    ("pytest.ini", "pytest"), ("pyproject.toml", "pytest"),
    ("setup.cfg", "pytest"), ("conftest.py", "pytest"),
    ("jest.config.js", "jest"), ("jest.config.ts", "jest"),
    ("vitest.config.js", "vitest"), ("vitest.config.ts", "vitest"),
    ("Cargo.toml", "cargo-test"), ("go.mod", "go-test"),
]

_LINTERS = [
    (".eslintrc.js", "eslint"), (".eslintrc.json", "eslint"),
    (".eslintrc.yml", "eslint"), ("eslint.config.js", "eslint"),
    (".pylintrc", "pylint"), ("pylintrc", "pylint"),
    ("mypy.ini", "mypy"), ("pyproject.toml", "mypy"),
    (".flake8", "flake8"), ("ruff.toml", "ruff"),
    ("rustfmt.toml", "rustfmt"), (".rustfmt.toml", "rustfmt"),
    ("golangci.yml", "golangci-lint"), (".golangci.yml", "golangci-lint"),
]


def detect_project(work_dir="."):
    """Detect project type and return info dict."""
    info = {
        "path": os.path.abspath(work_dir),
        "name": os.path.basename(os.path.abspath(work_dir)),
        "type": "unknown",
        "language": "unknown",
        "framework": None,
        "test_framework": None,
        "linters": [],
        "package_manager": None,
        "has_docker": False,
        "has_ci": False,
        "files": [],
    }

    if not os.path.isdir(work_dir):
        return info

    # Check for project files
    found_types = []
    for filename, lang, label in _DETECTIONS:
        fp = os.path.join(work_dir, filename)
        if os.path.exists(fp):
            found_types.append((lang, label))
            info["files"].append(filename)

    if found_types:
        info["type"] = found_types[0][0]
        info["language"] = found_types[0][1]

    # Test framework
    for filename, fw in _TEST_FRAMEWORKS:
        if os.path.exists(os.path.join(work_dir, filename)):
            info["test_framework"] = fw
            break

    # Linters
    for filename, linter in _LINTERS:
        if os.path.exists(os.path.join(work_dir, filename)):
            if linter not in info["linters"]:
                info["linters"].append(linter)

    # Docker
    info["has_docker"] = os.path.exists(os.path.join(work_dir, "Dockerfile"))

    # CI
    info["has_ci"] = os.path.isdir(os.path.join(work_dir, ".github", "workflows"))

    # Package manager detection
    if os.path.exists(os.path.join(work_dir, "yarn.lock")):
        info["package_manager"] = "yarn"
    elif os.path.exists(os.path.join(work_dir, "pnpm-lock.yaml")):
        info["package_manager"] = "pnpm"
    elif os.path.exists(os.path.join(work_dir, "package-lock.json")):
        info["package_manager"] = "npm"
    elif os.path.exists(os.path.join(work_dir, "poetry.lock")):
        info["package_manager"] = "poetry"
    elif os.path.exists(os.path.join(work_dir, "Pipfile.lock")):
        info["package_manager"] = "pipenv"
    elif os.path.exists(os.path.join(work_dir, "Cargo.lock")):
        info["package_manager"] = "cargo"

    # Parse package.json for framework detection
    pj = os.path.join(work_dir, "package.json")
    if os.path.exists(pj):
        try:
            with open(pj) as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            frameworks = {
                "next": "Next.js", "nuxt": "Nuxt.js", "gatsby": "Gatsby",
                "react": "React", "vue": "Vue.js", "angular": "Angular",
                "svelte": "Svelte", "express": "Express", "fastify": "Fastify",
                "nest": "NestJS", "remix": "Remix",
            }
            for key, name in frameworks.items():
                if key in deps:
                    info["framework"] = name
                    break
        except Exception:
            pass

    return info


def format_project_info(info):
    """Format project info as readable text."""
    lines = [f"Project: {info['name']}"]
    lines.append(f"Type: {info['language']}")
    if info["framework"]:
        lines.append(f"Framework: {info['framework']}")
    if info["package_manager"]:
        lines.append(f"Package Manager: {info['package_manager']}")
    if info["test_framework"]:
        lines.append(f"Test Framework: {info['test_framework']}")
    if info["linters"]:
        lines.append(f"Linters: {', '.join(info['linters'])}")
    if info["has_docker"]:
        lines.append("Docker: Yes")
    if info["has_ci"]:
        lines.append("CI/CD: GitHub Actions")
    if info["files"]:
        lines.append(f"Config files: {', '.join(info['files'][:10])}")
    return "\n".join(lines)


TOOL_NAMES = {"detect_project"}

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "detect_project",
            "description": "Auto-detect project type, language, framework, test framework, linters, and package manager from config files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Project root directory (default: current work_dir)"}
                }
            }
        }
    }
]


def execute(name, args, work_dir=None, bot=None):
    path = args.get("path", work_dir or ".")
    info = detect_project(path)
    return format_project_info(info)
