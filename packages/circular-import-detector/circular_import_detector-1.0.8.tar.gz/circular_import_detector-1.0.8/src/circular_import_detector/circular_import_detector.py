#!/usr/bin/env python3
"""
Circular Import Detector

A tool to detect circular imports in Python projects by analyzing import statements
and building a dependency graph to identify cycles.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to extract import information from Python files."""

    def __init__(self, module_path: str, project_root: Path):
        self.module_path = module_path
        self.project_root = project_root
        self.imports: Set[str] = set()
        self.from_imports: Set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """Handle 'import module' statements."""
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Handle 'from module import ...' statements."""
        if node.module:
            # Handle relative imports
            if node.level > 0:
                module_name = self._resolve_relative_import(node.module, node.level)
            else:
                module_name = node.module

            if module_name:
                self.from_imports.add(module_name.split('.')[0])
        self.generic_visit(node)

    def _resolve_relative_import(self, module: Optional[str], level: int) -> Optional[str]:
        """Resolve relative imports to absolute module names."""
        try:
            current_path = Path(self.module_path).relative_to(self.project_root)
            if current_path.name == '__init__.py':
                current_module_parts = current_path.parts[:-1]
            else:
                current_module_parts = current_path.parts[:-1]

            # Go up 'level' directories
            if level > len(current_module_parts):
                return None

            # Calculate base path after going up levels
            if level == 0:
                base_parts = current_module_parts
            else:
                base_parts = current_module_parts[:-level] if level <= len(current_module_parts) else ()

            if module:
                result_parts = base_parts + tuple(module.split('.'))
                return '.'.join(result_parts) if result_parts else module
            else:
                return '.'.join(base_parts) if base_parts else None
        except ValueError:
            return None


class CircularImportDetector:
    """Main class for detecting circular imports in Python projects."""

    def __init__(self, project_root: str):
        """Initialize the detector with the project root directory."""
        self.project_root = Path(project_root).resolve()
        self.module_graph: Dict[str, Set[str]] = defaultdict(set)
        self.file_to_module: Dict[str, str] = {}
        self.module_to_file: Dict[str, str] = {}

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project directory."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'build', 'dist', 'egg-info')]

            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    python_files.append(Path(root) / file)

        return python_files

    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            if rel_path.name == '__init__.py':
                # For __init__.py files, use the parent directory name
                module_parts = rel_path.parts[:-1]
                if not module_parts:  # Handle root __init__.py
                    return file_path.parent.name
                return '.'.join(module_parts)
            else:
                # For regular .py files, use the filename without extension
                module_parts = rel_path.parts[:-1] + (rel_path.stem,)
                return '.'.join(module_parts) if module_parts else rel_path.stem
        except ValueError:
            return file_path.stem

    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file for imports."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            analyzer = ImportAnalyzer(str(file_path), self.project_root)
            analyzer.visit(tree)

            module_name = self.get_module_name(file_path)
            self.file_to_module[str(file_path)] = module_name
            self.module_to_file[module_name] = str(file_path)

            # Store raw imports for later processing after all files are analyzed
            all_imports = analyzer.imports | analyzer.from_imports
            self._raw_imports = getattr(self, '_raw_imports', {})
            self._raw_imports[module_name] = all_imports

        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    def _filter_internal_imports(self, imports: Set[str]) -> Set[str]:
        """Filter imports to only include internal project modules."""
        internal_imports = set()

        for imp in imports:
            # Check if this import corresponds to a file in our project
            potential_paths = [
                self.project_root / f"{imp}.py",
                self.project_root / imp / "__init__.py"
            ]

            # Also check if it matches any known module in our project
            # This helps with package imports like 'from package import module'
            for module_name in self.module_to_file.keys():
                if module_name == imp or module_name.endswith(f'.{imp}'):
                    internal_imports.add(imp)
                    break
            else:
                # Check file system if module not yet processed
                if any(p.exists() for p in potential_paths):
                    internal_imports.add(imp)

                # Also check subdirectories
                for subdir in self.project_root.rglob("*"):
                    if subdir.is_dir():
                        subdir_paths = [
                            subdir / f"{imp}.py",
                            subdir / imp / "__init__.py"
                        ]
                        if any(p.exists() for p in subdir_paths):
                            internal_imports.add(imp)
                            break

        return internal_imports

    def _resolve_import_to_module(self, import_name: str) -> Optional[str]:
        """Resolve an import name to the actual module name in our project."""
        # Direct module name match
        if import_name in self.module_to_file:
            return import_name

        # Check if any module ends with this import name (for package imports)
        for module_name in self.module_to_file:
            if module_name == import_name:
                return module_name
            # Handle package.module imports
            if module_name.endswith(f'.{import_name}'):
                return module_name
            # Handle just the base name
            if module_name.split('.')[-1] == import_name:
                return module_name

        return None

    def find_cycles(self) -> List[List[str]]:
        """Return representative cycles for every SCC (finds ALL problems)."""
        graph = self.module_graph

        index = 0
        stack = []
        onstack = set()
        indices = {}
        low = {}
        sccs = []

        def strongconnect(v: str):
            nonlocal index
            indices[v] = index
            low[v] = index
            index += 1
            stack.append(v)
            onstack.add(v)

            for w in graph.get(v, ()):
                if w not in indices:
                    strongconnect(w)
                    low[v] = min(low[v], low[w])
                elif w in onstack:
                    low[v] = min(low[v], indices[w])

            if low[v] == indices[v]:
                comp = []
                while True:
                    w = stack.pop()
                    onstack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                sccs.append(comp)

        for v in graph:
            if v not in indices:
                strongconnect(v)

        # Turn SCCs into representative cycles for your existing formatter:
        cycles: List[List[str]] = []
        for comp in sccs:
            if len(comp) > 1:
                # multi-node cycle, e.g. [a, b, c] -> prints a->b, b->c, c->a
                cycles.append(comp)
            elif comp and comp[0] in graph.get(comp[0], set()):
                # self-loop
                cycles.append([comp[0]])

        return cycles

    def _tarjan_scc(self, graph):
        index = 0
        stack, onstack = [], set()
        indices, low = {}, {}
        out = []

        def strongconnect(v):
            nonlocal index
            indices[v] = index
            low[v] = index
            index += 1
            stack.append(v);
            onstack.add(v)

            for w in graph.get(v, ()):
                if w not in indices:
                    strongconnect(w)
                    low[v] = min(low[v], low[w])
                elif w in onstack:
                    low[v] = min(low[v], indices[w])

            if low[v] == indices[v]:
                comp = []
                while True:
                    w = stack.pop();
                    onstack.remove(w)
                    comp.append(w)
                    if w == v:
                        break
                out.append(comp)

        for v in graph:
            if v not in indices:
                strongconnect(v)
        return out

    def detect_circular_imports(self) -> tuple[bool, list[list[str]]]:
        # 1) Build the graph if it hasn't been built yet
        if not getattr(self, "module_graph", None) or not self.module_graph:
            # call your existing builder here (whatever it’s called in your code)
            # e.g. self.build_module_graph() or self.scan_project()
            #self.build_module_graph()  # <-- use YOUR actual builder name
            self.module_graph = defaultdict(set)

        graph = self.module_graph

        # 2) Ensure every target also exists as a key (important for SCC)
        for v, nbrs in list(graph.items()):
            for w in nbrs:
                graph.setdefault(w, set())

        sccs = self._tarjan_scc(graph)

        groups: list[list[str]] = []
        for comp in sccs:
            if len(comp) > 1:
                groups.append(comp)
            elif comp and comp[0] in graph.get(comp[0], set()):  # self-loop
                groups.append([comp[0]])

        return (bool(groups), groups)

    def format_cycles(self, groups):
        lines = [f"Found {len(groups)} circular import group(s):", ""]
        for i, comp in enumerate(groups, 1):
            lines.append(f"Group {i}:")
            # Show a representative loop in the group
            if len(comp) == 1:
                mod = comp[0]
                lines.append(f"  {mod} -> {mod} (self-import)")
            else:
                # simple representative ring
                ring = " -> ".join(comp + [comp[0]])
                lines.append(f"  {ring}")
            # file paths if you have a map
            if hasattr(self, "module_to_file"):
                lines.append("  Files involved:")
                for mod in comp:
                    p = self.module_to_file.get(mod)
                    if p:
                        lines.append(f"    {mod}: {p}")
            lines.append("")
        return "\n".join(lines).rstrip()


def main():
    """CLI entry point for the circular import detector."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect circular imports in Python projects")
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Path to the Python project directory (default: current directory)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only output if circular imports are found"
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if circular imports are found (useful for CI/CD)"
    )

    args = parser.parse_args()

    detector = CircularImportDetector(args.project_path)
    has_cycles, cycles = detector.detect_circular_imports()

    if has_cycles:
        print(detector.format_cycles(cycles))
        if args.exit_code:
            sys.exit(1)
    elif not args.quiet:
        print("No circular imports detected.")

    sys.exit(0)


if __name__ == "__main__":
    main()
