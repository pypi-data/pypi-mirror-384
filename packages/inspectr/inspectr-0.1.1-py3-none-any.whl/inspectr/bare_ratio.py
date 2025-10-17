#!/usr/bin/env python3
import ast
import pathlib
from collections import defaultdict, Counter
from typing import List


def main(files: List[pathlib.Path], **kwargs) -> None:
    for f in files:
        if not f.exists():
            print(f"Error: File does not exist: {f}")
            return
        
        if not f.is_file():
            print(f"Error: Not a file: {f}")
            return

    # distinct exception types
    exception_types = Counter()

    # Per-file counts
    bare_or_exception_per_file = defaultdict(int)
    other_exceptions_per_file = defaultdict(int)

    for f in files:
        src = f.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError:
            continue  # skip broken files

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except or except Exception
                if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception"):
                    bare_or_exception_per_file[f] += 1
                else:
                    # Count other exception types
                    if isinstance(node.type, ast.Tuple):
                        for elt in node.type.elts:
                            if isinstance(elt, ast.Name):
                                other_exceptions_per_file[f] += 1
                                exception_types[elt.id] += 1
                    elif isinstance(node.type, ast.Name):
                        other_exceptions_per_file[f] += 1
                        exception_types[node.type.id] += 1

    print("Distinct exception types used (excluding bare/Exception):")
    for exc, count in exception_types.most_common():
        print(f"  {exc}: {count} occurrence(s)")

    print("\nBare excepts / 'except Exception' ratio per file:")
    for f in sorted(set(list(bare_or_exception_per_file.keys()) + list(other_exceptions_per_file.keys()))):
        bare = bare_or_exception_per_file.get(f, 0)
        other = other_exceptions_per_file.get(f, 0)
        total = bare + other
        ratio = bare / total if total > 0 else 0
        print(f"  {f}: {bare} bare / {other} typed => ratio = {ratio:.2f}")

