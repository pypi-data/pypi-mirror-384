#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys

GITIGNORE = """__pycache__/
*.pyc
.env
venv/
.idea/
.DS_Store
"""

def default_name() -> str:
    count = sum(1 for p in Path(".").glob("lektion_*") if p.is_dir())
    return f"lektion_{count + 1}"

def create_scaffold(name: str, *, force: bool = False) -> None:
    root = Path(name)

    if root.exists() and not force:
        print(f"Error: '{name}' already exists. Use --force to proceed.", file=sys.stderr)
        sys.exit(1)

    (root / "application" / "static").mkdir(parents=True, exist_ok=True)
    (root / "application" / "templates").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)

    (root / "application" / "__init__.py").touch(exist_ok=True)
    (root / "application" / "app.py").touch(exist_ok=True)

    gi = root / ".gitignore"
    if not gi.exists() or force:
        gi.write_text(GITIGNORE)

    print(f"Created {name} with .gitignore")
    print("Next steps:")
    print(f"  cd {name}")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate")

def main():
    parser = argparse.ArgumentParser(description="Create a lektion project scaffold.")
    parser.add_argument("name", nargs="?", help="Project name (default: auto lektion_N)")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files if present.")
    args = parser.parse_args()

    create_scaffold(args.name or default_name(), force=args.force)

if __name__ == "__main__":
    main()
