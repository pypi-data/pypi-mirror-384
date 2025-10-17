#!/usr/bin/env python3
import ast
import pathlib
from collections import Counter, defaultdict
from typing import List


def main(files: List[pathlib.Path], **kwargs) -> None:
    for f in files:
        if not f.exists():
            print(f"Error: File does not exist: {f}")
            return
        
        if not f.is_file():
            print(f"Error: Not a file: {f}")
            return

    exception_types = Counter()
    bare_or_exception_per_file = defaultdict(int)

    for f in files:
        src = f.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError:
            continue  # skip broken files

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except
                if node.type is None:
                    bare_or_exception_per_file[f] += 1
                # except Exception
                elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    bare_or_exception_per_file[f] += 1
                else:
                    # record the exception type (support multiple names in tuple)
                    if isinstance(node.type, ast.Tuple):
                        for elt in node.type.elts:
                            if isinstance(elt, ast.Name):
                                exception_types[elt.id] += 1
                    elif isinstance(node.type, ast.Name):
                        exception_types[node.type.id] += 1

    print("Distinct exception types used:")
    for exc, count in exception_types.most_common():
        print(f"  {exc}: {count} occurrence(s)")

    print("\nBare excepts or 'except Exception' per file:")
    for f, count in sorted(bare_or_exception_per_file.items()):
        print(f"  {f}: {count}")

