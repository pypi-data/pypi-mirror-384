import tempfile
import pathlib
import pytest
from inspectr.size_counts import main


def test_small_file(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Summary:" in output
    finally:
        path.unlink()


def test_function_with_params(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo(a, b, c):\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Summary:" in output
    finally:
        path.unlink()


def test_function_with_many_params(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo(a, b, c, d, e, f, g):\n    pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "7 parameters" in output
    finally:
        path.unlink()


def test_class_with_methods(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("class Foo:\n    def method1(self):\n        pass\n    def method2(self):\n        pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Summary:" in output
    finally:
        path.unlink()


def test_validates_file_exists(capsys):
    path = pathlib.Path("/nonexistent/file.py")
    main([path])
    output = capsys.readouterr().out
    assert "does not exist" in output


def test_large_function(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n")
        for i in range(60):
            f.write(f"    x{i} = {i}\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "60 lines" in output
    finally:
        path.unlink()


def test_large_file(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        for i in range(1100):
            f.write(f"x{i} = {i}\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "1100 lines" in output
    finally:
        path.unlink()


def test_class_with_private_methods(capsys):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("class Foo:\n    def public(self):\n        pass\n    def _private(self):\n        pass\n")
        path = pathlib.Path(f.name)
    
    try:
        main([path])
        output = capsys.readouterr().out
        assert "Summary:" in output
    finally:
        path.unlink()
