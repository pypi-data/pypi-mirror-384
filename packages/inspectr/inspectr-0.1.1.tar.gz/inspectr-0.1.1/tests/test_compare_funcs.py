import tempfile
import pathlib
import os
import pytest
from inspectr.compare_funcs import extract_functions, compare_functions, main


def test_extract_functions_simple():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    pass\n\ndef bar():\n    pass\n")
        path = f.name
    
    try:
        funcs = extract_functions(path)
        assert 'foo' in funcs
        assert 'bar' in funcs
    finally:
        os.unlink(path)


def test_extract_functions_async():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("async def async_foo():\n    pass\n")
        path = f.name
    
    try:
        funcs = extract_functions(path)
        assert 'async_foo' in funcs
    finally:
        os.unlink(path)


def test_extract_functions_class_methods():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("class MyClass:\n    def method(self):\n        pass\n")
        path = f.name
    
    try:
        funcs = extract_functions(path)
        assert 'method' in funcs
    finally:
        os.unlink(path)


def test_extract_functions_syntax_error():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def broken(\n")
        path = f.name
    
    try:
        funcs = extract_functions(path)
        assert len(funcs) == 0
    finally:
        os.unlink(path)


def test_extract_functions_nonexistent():
    funcs = extract_functions("/nonexistent/file.py")
    assert len(funcs) == 0


def test_main_insufficient_args(capsys):
    main([])
    output = capsys.readouterr().out
    assert "Usage:" in output


def test_main_nonexistent_file_list(capsys):
    path = pathlib.Path("/nonexistent/list.txt")
    dir1 = pathlib.Path("/tmp")
    dir2 = pathlib.Path("/tmp")
    main([path, dir1, dir2])
    output = capsys.readouterr().out
    assert "does not exist" in output


def test_main_dir_not_directory(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("test.py\n")
        list_path = pathlib.Path(f.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        not_dir = pathlib.Path(f.name)
    
    try:
        main([list_path, not_dir, pathlib.Path("/tmp")])
        output = capsys.readouterr().out
        assert "Not a directory" in output
    finally:
        list_path.unlink()
        not_dir.unlink()
