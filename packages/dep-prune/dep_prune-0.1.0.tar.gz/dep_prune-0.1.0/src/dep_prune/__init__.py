#!/usr/bin/env python3
"""
Analyze Python project to find potentially unused dependencies in pyproject.toml.

This tool scans all Python files in a project, extracts imports, and compares
them against dependencies declared in pyproject.toml to identify potentially
unused packages.
"""

import argparse
import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import toml


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract all imports from Python code."""

    def __init__(self):
        self.imports = set()
        self.from_imports = defaultdict(set)

    def visit_Import(self, node):
        """Handle 'import x' statements."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Handle 'from x import y' statements."""
        if node.module:
            self.imports.add(node.module)
            for alias in node.names:
                if alias.name != "*":
                    self.from_imports[node.module].add(alias.name)
        self.generic_visit(node)


def extract_imports_from_file(filepath: Path) -> Tuple[Set[str], Dict[str, Set[str]]]:
    """Extract all imports from a Python file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        visitor = ImportVisitor()
        visitor.visit(tree)

        return visitor.imports, visitor.from_imports
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)
        return set(), {}


def find_python_files(root_dir: Path, exclude_dirs: Set[str] = None) -> List[Path]:
    """Recursively find all Python files in a directory."""
    if exclude_dirs is None:
        exclude_dirs = {
            ".git",
            "__pycache__",
            ".tox",
            "venv",
            "env",
            ".venv",
            "build",
            "dist",
            "*.egg-info",
            "node_modules",
        }

    python_files = []

    for root, dirs, files in os.walk(root_dir):
        # Remove excluded directories from dirs to prevent walking into them
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.endswith(".egg-info")]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def normalize_package_name(name: str) -> str:
    """
    Normalize package name for comparison.
    PyPI package names can have hyphens or underscores, and are case-insensitive.
    """
    return name.lower().replace("-", "_").replace(".", "_")


def get_root_package(import_name: str) -> str:
    """Get the root package from an import statement."""
    parts = import_name.split(".")
    return parts[0]


def load_pyproject_dependencies(pyproject_path: Path) -> Dict[str, List[str]]:
    """Load dependencies from pyproject.toml."""
    try:
        with open(pyproject_path, "r") as f:
            data = toml.load(f)
    except FileNotFoundError:
        print(f"Error: {pyproject_path} not found", file=sys.stderr)
        sys.exit(1)
    except toml.TomlDecodeError as e:
        print(f"Error parsing {pyproject_path}: {e}", file=sys.stderr)
        sys.exit(1)

    dependencies = {}

    # Handle different pyproject.toml formats

    # Poetry format
    if "tool" in data and "poetry" in data["tool"]:
        poetry = data["tool"]["poetry"]
        if "dependencies" in poetry:
            dependencies["main"] = list(poetry["dependencies"].keys())
        if "dev-dependencies" in poetry:
            dependencies["dev"] = list(poetry["dev-dependencies"].keys())
        if "group" in poetry:
            for group_name, group_data in poetry["group"].items():
                if "dependencies" in group_data:
                    dependencies[f"group.{group_name}"] = list(group_data["dependencies"].keys())

    # PEP 621 format (setuptools, flit, hatch, etc.)
    if "project" in data:
        project = data["project"]
        if "dependencies" in project:
            # Parse dependency specifications (remove version constraints)
            deps = []
            for dep in project["dependencies"]:
                # Extract package name from specifications like "package>=1.0"
                match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                if match:
                    deps.append(match.group(1))
            dependencies["main"] = deps

        if "optional-dependencies" in project:
            for extra, deps_list in project["optional-dependencies"].items():
                deps = []
                for dep in deps_list:
                    match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                    if match:
                        deps.append(match.group(1))
                dependencies[f"optional.{extra}"] = deps

    # PDM format
    if "tool" in data and "pdm" in data["tool"]:
        pdm = data["tool"]["pdm"]
        if "dev-dependencies" in pdm:
            for group_name, deps_list in pdm["dev-dependencies"].items():
                deps = []
                for dep in deps_list:
                    match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                    if match:
                        deps.append(match.group(1))
                dependencies[f"dev.{group_name}"] = deps

    # Remove Python itself and special dependencies
    for group in dependencies:
        dependencies[group] = [
            dep
            for dep in dependencies[group]
            if dep.lower() not in ["python", "pip", "setuptools", "wheel"]
        ]

    return dependencies


# Common package name mappings (import name -> package name)
PACKAGE_MAPPINGS = {
    "cv2": "opencv-python",
    "cv": "opencv-python",
    "PIL": "pillow",
    "Image": "pillow",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
    "jose": "python-jose",
    "multipart": "python-multipart",
    "magic": "python-magic",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "xlsx": "openpyxl",
    "jwt": "pyjwt",
    "crypto": "pycryptodome",
    "Crypto": "pycryptodome",
    "zmq": "pyzmq",
    "serial": "pyserial",
    "usb": "pyusb",
    "git": "gitpython",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "graphene": "graphene",
    "graphql": "graphql-core",
    "mpl_toolkits": "matplotlib",
    "google": "google-api-python-client",
    "googleapiclient": "google-api-python-client",
    "telegram": "python-telegram-bot",
    "discord": "discord.py",
    "slack": "slack-sdk",
    "ldap": "python-ldap",
    "ldap3": "ldap3",
    "MySQLdb": "mysqlclient",
    "psycopg2": "psycopg2-binary",
    "werkzeug": "werkzeug",
    "jinja2": "jinja2",
    "markupsafe": "markupsafe",
    "itsdangerous": "itsdangerous",
    "click": "click",
    "flask": "flask",
    "django": "django",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "starlette": "starlette",
    "pydantic": "pydantic",
    "httpx": "httpx",
    "aiohttp": "aiohttp",
    "tornado": "tornado",
    "bottle": "bottle",
    "cherrypy": "cherrypy",
    "pyramid": "pyramid",
    "dash": "dash",
    "streamlit": "streamlit",
    "gradio": "gradio",
}


def match_import_to_package(import_name: str, packages: List[str]) -> bool:
    """Check if an import matches any of the declared packages."""
    root_import = get_root_package(import_name)
    normalized_import = normalize_package_name(root_import)

    for package in packages:
        normalized_package = normalize_package_name(package)

        # Direct match
        if normalized_import == normalized_package:
            return True

        # Check if import is a submodule of package
        if normalized_import.startswith(normalized_package + "_"):
            return True

        # Check known mappings
        if root_import in PACKAGE_MAPPINGS:
            mapped_package = normalize_package_name(PACKAGE_MAPPINGS[root_import])
            if mapped_package == normalized_package:
                return True

    return False


def analyze_dependencies(root_dir: Path, pyproject_path: Path, verbose: bool = False) -> None:
    """Main function to analyze dependencies."""
    print(f"Analyzing project at: {root_dir}")
    print(f"Reading pyproject.toml from: {pyproject_path}\n")

    # Load dependencies from pyproject.toml
    dependencies = load_pyproject_dependencies(pyproject_path)

    if not dependencies:
        print("No dependencies found in pyproject.toml")
        return

    print("Found dependency groups:")
    for group, deps in dependencies.items():
        print(f"  {group}: {len(deps)} packages")
    print()

    # Find all Python files
    python_files = find_python_files(root_dir)
    print(f"Found {len(python_files)} Python files\n")

    # Extract all imports
    all_imports = set()
    import_locations = defaultdict(list)

    for filepath in python_files:
        imports, from_imports = extract_imports_from_file(filepath)
        for imp in imports:
            all_imports.add(imp)
            relative_path = filepath.relative_to(root_dir)
            import_locations[imp].append(str(relative_path))

    # Get unique root packages from imports
    root_imports = {get_root_package(imp) for imp in all_imports}

    if verbose:
        print("All imported packages (root level):")
        for imp in sorted(root_imports):
            print(f"  {imp}")
        print()

    # Analyze each dependency group
    for group, packages in dependencies.items():
        print(f"\n{'=' * 60}")
        print(f"Analyzing {group} dependencies:")
        print(f"{'=' * 60}")

        used_packages = []
        potentially_unused = []

        for package in packages:
            is_used = False
            for import_name in root_imports:
                if match_import_to_package(import_name, [package]):
                    is_used = True
                    used_packages.append(package)
                    break

            if not is_used:
                potentially_unused.append(package)

        # Report results
        if used_packages:
            print(f"\n✓ Used packages ({len(used_packages)}):")
            for package in sorted(used_packages):
                print(f"  • {package}")

        if potentially_unused:
            print(f"\n⚠ Potentially unused packages ({len(potentially_unused)}):")
            for package in sorted(potentially_unused):
                print(f"  • {package}")
                if verbose:
                    # Try to find partial matches for debugging
                    normalized_pkg = normalize_package_name(package)
                    partial_matches = [
                        imp
                        for imp in root_imports
                        if normalized_pkg in normalize_package_name(imp)
                        or normalize_package_name(imp) in normalized_pkg
                    ]
                    if partial_matches:
                        print(f"    (Partial matches found: {', '.join(partial_matches)})")

        print(f"\nSummary for {group}:")
        print(f"  Total: {len(packages)}")
        print(f"  Used: {len(used_packages)}")
        print(f"  Potentially unused: {len(potentially_unused)}")

    # Show imports that don't match any declared dependency
    if verbose:
        print(f"\n{'=' * 60}")
        print("Imports without matching dependencies:")
        print(f"{'=' * 60}")

        all_packages = []
        for packages in dependencies.values():
            all_packages.extend(packages)

        unmatched = []
        for import_name in root_imports:
            if not any(match_import_to_package(import_name, all_packages) for _ in [None]):
                # Skip standard library modules (basic heuristic)
                if not import_name.startswith("_") and import_name not in [
                    "os",
                    "sys",
                    "re",
                    "json",
                    "math",
                    "random",
                    "datetime",
                    "time",
                    "collections",
                    "itertools",
                    "functools",
                    "pathlib",
                    "typing",
                    "ast",
                    "subprocess",
                    "argparse",
                    "logging",
                    "unittest",
                    "copy",
                    "shutil",
                    "tempfile",
                    "contextlib",
                    "warnings",
                    "abc",
                    "enum",
                    "dataclasses",
                    "decimal",
                    "fractions",
                    "statistics",
                    "string",
                    "textwrap",
                    "unicodedata",
                    "codecs",
                    "io",
                    "glob",
                    "fnmatch",
                    "pickle",
                    "csv",
                    "configparser",
                    "hashlib",
                    "hmac",
                    "secrets",
                    "uuid",
                    "urllib",
                    "http",
                    "email",
                    "base64",
                    "binascii",
                    "zlib",
                    "gzip",
                    "tarfile",
                    "zipfile",
                    "sqlite3",
                    "xml",
                    "html",
                    "webbrowser",
                    "platform",
                    "socket",
                    "ssl",
                    "asyncio",
                    "concurrent",
                    "multiprocessing",
                    "threading",
                    "queue",
                    "signal",
                    "traceback",
                    "inspect",
                    "importlib",
                    "types",
                    "weakref",
                    "gc",
                    "builtins",
                    "__future__",
                    "setuptools",
                ]:
                    unmatched.append(import_name)

        if unmatched:
            print("\nPossibly missing from pyproject.toml:")
            for imp in sorted(unmatched):
                locations = import_locations[imp]
                print(f"  • {imp}")
                if len(locations) <= 3:
                    for loc in locations[:3]:
                        print(f"    used in: {loc}")
                else:
                    print(f"    used in: {locations[0]} (and {len(locations) - 1} other files)")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Python project dependencies and find potentially unused packages in pyproject.toml"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the project directory (default: current directory)",
    )
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to pyproject.toml file (default: pyproject.toml in project root)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    root_dir = Path(args.path).resolve()
    if not root_dir.is_dir():
        print(f"Error: {root_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Handle pyproject.toml path
    if os.path.isabs(args.pyproject):
        pyproject_path = Path(args.pyproject)
    else:
        pyproject_path = root_dir / args.pyproject

    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} not found", file=sys.stderr)
        sys.exit(1)

    analyze_dependencies(root_dir, pyproject_path, verbose=args.verbose)


if __name__ == "__main__":
    main()
