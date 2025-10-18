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
    p = argparse.ArgumentParser(description="Pre-commit hook for circular imports")
    p.add_argument("filenames", nargs="*")
    p.add_argument("--repo-root", default=".")
    args = p.parse_args()

    repo_root = Path(args.repo_root).resolve()

    # Build full graph once (correct relationships across the project)
    det = CircularImportDetector(str(repo_root))
    has_cycles, groups = det.detect_circular_imports()

    # Map changed files -> modules
    file_to_mod = {}
    if hasattr(det, "module_to_file"):
        # invert {module -> file}
        file_to_mod = {Path(fp).resolve(): mod for mod, fp in det.module_to_file.items()}

    changed_modules = set()
    for f in args.filenames:
        pf = Path(f).resolve()
        if pf in file_to_mod:
            changed_modules.add(file_to_mod[pf])
        else:
            # Fallback: derive module name from repo layout
            try:
                rel = pf.relative_to(repo_root)
                parts = list(rel.parts)
                if parts and parts[0] == "src" and len(parts) >= 2:
                    parts = parts[1:]  # drop 'src'
                if parts and parts[-1].endswith(".py"):
                    parts[-1] = parts[-1][:-3]  # strip .py
                mod = ".".join(p for p in parts if p and p != "__init__")
                if mod:
                    changed_modules.add(mod)
            except Exception:
                pass

    # Filter to groups that touch any changed module (if any were mapped)
    if changed_modules:
        groups = [g for g in groups if any(m in changed_modules for m in g)]
        has_cycles = bool(groups)

    if has_cycles:
        print(det.format_cycles(groups))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
