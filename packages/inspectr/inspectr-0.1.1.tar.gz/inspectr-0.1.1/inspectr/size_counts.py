#!/usr/bin/env python3
import ast
import pathlib
from typing import List

# TODO: put these in a config file
# Thresholds
LINE_THRESHOLD = 1000
METHOD_LINES = 50
FUNC_PARAMS = 5
CLASS_METHODS = 20


def main(files: List[pathlib.Path], **kwargs) -> None:
    for f in files:
        if not f.exists():
            print(f"Error: File does not exist: {f}")
            return
        
        if not f.is_file():
            print(f"Error: Not a file: {f}")
            return

    # TODO: rename these
    # Counters and diagnostics
    files_over_1000 = []
    methods_over_50 = []
    functions_over_5params = []
    classes_over_20methods = []

    for fname in files:
        with open(fname, "r", encoding="utf-8") as f:
            src = f.read()
        lines = src.splitlines()
        if len(lines) > LINE_THRESHOLD:
            files_over_1000.append((fname, len(lines)))

        tree = ast.parse(src, filename=fname)
        for node in ast.walk(tree):
            # Functions
            if isinstance(node, ast.FunctionDef):
                n_params = len(node.args.args)
                n_lines = len(node.body) if hasattr(node, "body") else 0

                if n_params > FUNC_PARAMS:
                    functions_over_5params.append((fname, node.name, n_params))
                if n_lines > METHOD_LINES:
                    methods_over_50.append((fname, node.name, n_lines))

            # Classes
            if isinstance(node, ast.ClassDef):
                public_methods = [
                    n for n in node.body
                    if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
                ]
                n_public_methods = len(public_methods)
                if n_public_methods > CLASS_METHODS:
                    method_names = [m.name for m in public_methods]
                    classes_over_20methods.append((fname, node.name, n_public_methods, method_names))

    # Print diagnostics if counts > 0
    if files_over_1000:
        print(f"Files > {LINE_THRESHOLD} lines:")
        for fname, nlines in files_over_1000:
            print(f"  {fname}: {nlines} lines")

    if methods_over_50:
        print(f"\nMethods > {METHOD_LINES} lines:")
        for fname, name, nlines in methods_over_50:
            print(f"  {fname}.{name}: {nlines} lines")

    if functions_over_5params:
        print(f"\nFunctions > {FUNC_PARAMS} parameters:")
        for fname, name, nparams in functions_over_5params:
            print(f"  {fname}.{name}: {nparams} parameters")

    if classes_over_20methods:
        print(f"\nClasses > {CLASS_METHODS} public methods:")
        for fname, cls_name, nmethods, method_names in classes_over_20methods:
            print(f"  {fname}.{cls_name}: {nmethods} public methods -> {', '.join(method_names)}")

    # Summary
    print("\nSummary:")
    print(f"  Files > {LINE_THRESHOLD} lines: {len(files_over_1000)}")
    print(f"  Methods > {METHOD_LINES} lines: {len(methods_over_50)}")
    print(f"  Functions > {FUNC_PARAMS} parameters: {len(functions_over_5params)}")
    print(f"  Classes > {CLASS_METHODS} public methods: {len(classes_over_20methods)}")

