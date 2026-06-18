"""
Scaffold AI collaboration docs for a new project.

Creates in project root:
  AGENTS.md
  CLAUDE.md
  ai-doc/
    MEMORY.md
    topic/
      topic_writing_rule.md

Usage:
    python new_project.py                  # project root = parent of ai-env
    python new_project.py /path/to/project
    python new_project.py --force          # overwrite existing files
"""

import argparse
import shutil
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "ai-doc/MEMORY.md",
    "ai-doc/topic/topic_writing_rule.md",
]


def scaffold(project_root: Path, force: bool = False):
    project_root = project_root.resolve()

    print(f"[scaffold] Project root : {project_root}")
    print()

    created, skipped = [], []

    for rel in FILES:
        src = TEMPLATES_DIR / rel
        dst = project_root / rel

        if not src.exists():
            print(f"[warn] Template not found: {src}")
            continue

        if dst.exists() and not force:
            skipped.append(rel)
            print(f"[skip]  {rel}  (already exists, use --force to overwrite)")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        created.append(rel)
        print(f"[create] {rel}")

    print()
    if created:
        print(f"Created {len(created)} file(s).")
        print()
        print("Next steps:")
        print("  1. Edit CLAUDE.md — fill in Project Overview, Dev Commands, Architecture")
        print("  2. Edit AGENTS.md — adjust rules for this project if needed")
        print("  3. Run /init in Claude Code to update CLAUDE.md with codebase context")
        print("  4. In Claude, enter: 閱讀 ai-env/ai-env-guide.md，了解可用工具與環境設定")
    if skipped:
        print(f"Skipped {len(skipped)} existing file(s). Use --force to overwrite.")


def main():
    parser = argparse.ArgumentParser(description="Scaffold AI collaboration docs")
    parser.add_argument("project", nargs="?", help="Project root (default: parent of ai-env)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    aienv_dir = Path(__file__).resolve().parents[1]
    project_root = Path(args.project) if args.project else aienv_dir.parent

    scaffold(project_root, force=args.force)


if __name__ == "__main__":
    main()
