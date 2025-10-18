#!/usr/bin/env python3
"""
Pre-commit hook wrapper for the circular import detector.

This script is designed to be called by pre-commit and will analyze only
the files that are being committed.
"""

import sys
import argparse
from pathlib import Path
from .circular_import_detector import CircularImportDetector


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-commit hook for circular imports")
    parser.add_argument("filenames", nargs="*")           # pre-commit passes these
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    # If nothing staged, do nothing (allow commit)
    if not args.filenames:
        return 0

    detector = CircularImportDetector(project_path=Path(args.repo_root).resolve())

    has_cycles, groups = detector.detect_circular_imports()  # your existing method

    # Map changed files -> modules using your existing module_to_file map
    # (you already print file paths per module, so this exists somewhere)
    file_to_module = {}
    for mod, p in getattr(detector, "module_to_file", {}).items():
        file_to_module[Path(p).resolve()] = mod

    changed_modules = set()
    for f in args.filenames:
        p = Path(f).resolve()
        if p in file_to_module:
            changed_modules.add(file_to_module[p])

    # If we couldn't map, fall back to scanning whole repo (rare).
    if not changed_modules:
        # Option A: allow commit
        # return 0
        # Option B (stricter): check whole repo
        pass

    # Keep only cycles that touch a changed module
    if changed_modules:
        groups = [g for g in groups if any(m in changed_modules for m in g)]
        has_cycles = bool(groups)

    if has_cycles:
        print(detector.format_cycles(groups))
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
