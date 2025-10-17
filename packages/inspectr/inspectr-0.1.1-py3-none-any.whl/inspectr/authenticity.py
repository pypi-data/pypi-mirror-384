#!/usr/bin/env python3
import ast
import pathlib
from typing import List


def main(files: List[pathlib.Path], **kwargs) -> None:
    for f in files:
        if not f.exists():
            print(f"Error: file does not exist: {f}")
            return
        if not f.is_file():
            print(f"Error: not a file: {f}")
            return

    todo_count = 0
    fixme_count = 0
    placeholder_count = 0
    empty_try_except_count = 0
    stub_functions = []

    for f in files:
        src = f.read_text(encoding="utf-8")

        # TODO: make these case insensitive
        todo_count += src.count("TODO")
        fixme_count += src.count("FIXME")
        placeholder_count += src.count("Placeholder")

        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError:
            continue  # skip broken files

        for node in ast.walk(tree):
            # Empty try/except blocks
            if isinstance(node, ast.Try):
                try_empty = len(node.body) == 0
                except_empty = all(len(h.body) == 0 or all(isinstance(s, ast.Pass) for s in h.body) for h in node.handlers)
                if try_empty and except_empty:
                    empty_try_except_count += 1

            # Stub functions/methods
            if isinstance(node, ast.FunctionDef):
                # Only consider body statements that are `pass` or empty return
                is_stub = True
                non_docstring_seen = False
                for i, stmt in enumerate(node.body):
                    if isinstance(stmt, ast.Pass):
                        non_docstring_seen = True
                        continue
                    elif isinstance(stmt, ast.Return) and stmt.value is None:
                        non_docstring_seen = True
                        continue
                    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        # ignore docstrings
                        if i == 0 or (i == 1 and not non_docstring_seen):
                            continue
                        else:
                            is_stub = False
                            break
                    else:
                        is_stub = False
                        break
                if is_stub and len(node.body) > 0:
                    stub_functions.append(f"{f}:{node.name}")

    print("Analysis results:")
    print(f"  TODO comments: {todo_count}")
    print(f"  FIXME comments: {fixme_count}")
    print(f"  Placeholder comments: {placeholder_count}")
    print(f"  Empty try/except blocks: {empty_try_except_count}")
    print(f"  Stub functions/methods: {len(stub_functions)}")
    for stub in stub_functions:
        print(f"    {stub}")
